import asyncio
import logging
from typing import List, Dict, Any

import aiohttp

from config.settings import settings
from services.supabase_service import SupabaseService
from services.crypto_service import CryptoService


logger = logging.getLogger(__name__)


class Trc20Monitor:
    """Периодическая проверка входящих USDT (TRC20) переводов на адрес из настроек.

    Логика сопоставления проста: ищем входящие на наш адрес переводы USDT и матчим
    с ожидающими (pending) платежами по сумме (± tolerance). При совпадении активируем подписку.
    """

    USDT_TRC20_CONTRACT = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'

    def __init__(self, interval_seconds: int = 180) -> None:
        self.supabase_service = SupabaseService()
        self.crypto = CryptoService()
        self.interval_seconds = interval_seconds
        self._task = None
        self._stopped = asyncio.Event()

    async def start(self) -> None:
        if not settings.ENABLE_TRC20_MONITOR or not settings.CRYPTO_TRC20_USDT_ADDRESS:
            logger.info("TRC20 монитор отключён или не настроен адрес")
            return
        if self._task and not self._task.done():
            return
        self._stopped.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("TRC20 монитор запущен (каждые %s сек)", self.interval_seconds)

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            try:
                await self._task
            except Exception:
                pass

    async def _run_loop(self) -> None:
        while not self._stopped.is_set():
            try:
                await self._check_once()
            except Exception as e:
                logger.error(f"TRC20 monitor loop error: {e}")
            await asyncio.wait([self._stopped.wait()], timeout=self.interval_seconds)

    async def _check_once(self) -> None:
        address = settings.CRYPTO_TRC20_USDT_ADDRESS
        if not address:
            return

        pending = self.supabase_service.supabase.table('payments').select('*').eq('payment_method', 'crypto').eq('status', 'pending').order('created_at', desc=True).limit(50).execute()
        pending_list: List[Dict[str, Any]] = pending.data or []
        if not pending_list:
            return

        url = (
            'https://apilist.tronscanapi.com/api/token_trc20/transfers'
            f'?limit=50&start=0&sort=-timestamp&count=true&relatedAddress={address}'
            f'&contract_address={self.USDT_TRC20_CONTRACT}'
        )
        headers = {}
        if settings.TRONGRID_API_KEY:
            headers['TRON-PRO-API-KEY'] = settings.TRONGRID_API_KEY

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=20) as resp:
                if resp.status != 200:
                    logger.warning(f'TronScan status: {resp.status}')
                    return
                data = await resp.json()

        transfers = (data or {}).get('token_transfers', [])
        incoming: List[Dict[str, Any]] = []
        for t in transfers:
            try:
                to_addr = t.get('to_address')
                if not to_addr or to_addr.lower() != address.lower():
                    continue
                decimals = int(t.get('tokenInfo', {}).get('tokenDecimal', 6))
                quant = float(t.get('quant', 0))
                amount = quant / (10 ** decimals)
                incoming.append({
                    'tx_hash': t.get('transaction_id'),
                    'amount': amount,
                    'timestamp_ms': t.get('block_ts'),
                })
            except Exception:
                continue

        if not incoming:
            return

        tolerance = getattr(settings, 'TRC20_AMOUNT_TOLERANCE_USD', 0.5)
        for pay in pending_list:
            try:
                price = float(pay.get('amount', 0))
                match = next((inc for inc in incoming if abs(inc['amount'] - price) <= tolerance), None)
                if not match:
                    continue
                ok = await self.crypto.activate_after_user_confirm(user_id=pay['user_id'], plan_type=(pay.get('plan_type') or 'monthly'), tx_hash=match['tx_hash'])
                if ok:
                    self.supabase_service.supabase.table('payments').update({'status': 'completed', 'tx_hash': match['tx_hash']}).eq('id', pay['id']).execute()
                    logger.info(f"TRC20 подтверждён: user={pay['user_id']} tx={match['tx_hash']}")
            except Exception as e:
                logger.error(f'TRC20 match error: {e}')


