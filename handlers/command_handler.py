from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from services.supabase_service import SupabaseService
from services.subscription_service import SubscriptionService
from utils.report_generator import ReportGenerator
from models.data_models import User
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.subscription_service = SubscriptionService()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        try:
            user = update.effective_user
            
            # Проверяем, существует ли пользователь в БД
            existing_user = await self.supabase_service.get_user_by_telegram_id(user.id)
            
            if not existing_user:
                # Создаем нового пользователя
                new_user = User(
                    telegram_id=user.id,
                    username=user.username
                )
                await self.supabase_service.create_user(new_user)
                logger.info(f"Создан новый пользователь: {user.id}")
            
            welcome_message = ReportGenerator.get_welcome_message()
            keyboard = [
                [InlineKeyboardButton(text="➕ Вода +250мл", callback_data="water_add_250")],
                [InlineKeyboardButton(text="📋 Меню", callback_data="open_menu")]
            ]
            await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            
        except Exception as e:
            logger.error(f"Ошибка в команде start: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        try:
            help_message = ReportGenerator.get_help_message()
            await update.message.reply_text(help_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Ошибка в команде help: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback-кнопок"""
        try:
            logger.info("🔍 Callback-обработчик запущен")
            query = update.callback_query
            user = update.effective_user
            logger.info(f"🔍 Пользователь: {user.id}, callback_data: {query.data}")
            
            # Сразу отвечаем на callback чтобы убрать "часики" у кнопки
            await query.answer()
            logger.info("✅ query.answer() выполнен")
            
            # Получаем пользователя из БД
            logger.info("🔍 Получаю пользователя из БД...")
            db_user = await self.supabase_service.get_user_by_telegram_id(user.id)
            if not db_user:
                logger.error("❌ Пользователь не найден в БД")
                await query.edit_message_text("❌ Пользователь не найден. Используйте /start для регистрации.")
                return
            logger.info(f"✅ Пользователь найден в БД: {db_user.id}")

            data = query.data
            logger.info(f"🎯 Обрабатываю callback: {data} от пользователя {user.id}")
            if data == "water_add_250":
                # Добавляем воду
                logger.info("💧 Добавляю воду...")
                await self.supabase_service.add_water_intake(db_user.id, 250)
                logger.info("✅ Вода добавлена в БД")
                
                water_today = await self.supabase_service.get_water_today(db_user.id)
                logger.info(f"📊 Вода за сегодня: {water_today}мл")
                
                text = ReportGenerator.format_water_status(water_today, db_user.daily_water_goal_ml)
                logger.info("✅ Статус воды сформирован")
                
                keyboard = [
                    [InlineKeyboardButton(text="➕ Вода +250мл", callback_data="water_add_250")],
                    [InlineKeyboardButton(text="📋 Меню", callback_data="open_menu")]
                ]
                logger.info("🔘 Клавиатура создана")
                
                await query.edit_message_text(
                    text=f"💧 Вода добавлена!\n\n{text}", 
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                logger.info("✅ Сообщение обновлено")
                return

            if data == "open_menu":
                # Главное меню
                logger.info("📋 Открываю главное меню...")
                keyboard = [
                    [InlineKeyboardButton(text="📊 День: калории/вода", callback_data="menu_day")],
                    [InlineKeyboardButton(text="📈 Неделя: график", callback_data="menu_week")],
                    [InlineKeyboardButton(text="⚙️ Настройки воды", callback_data="menu_settings_water")],
                ]
                logger.info("🔘 Меню создано")
                await query.edit_message_text(
                    text="📋 *Главное меню*\n\nВыберите раздел:", 
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                logger.info("✅ Меню отображено")
                return

            if data == "menu_day":
                # День: калории + вода
                nutrition_data = await self.supabase_service.get_user_nutrition_today(db_user.id)
                user_goals = {
                    'calories': db_user.daily_calories_goal,
                    'protein': db_user.daily_protein_goal,
                    'fats': db_user.daily_fats_goal,
                    'carbs': db_user.daily_carbs_goal
                }
                report = ReportGenerator.format_daily_report(nutrition_data, user_goals)
                water_today = await self.supabase_service.get_water_today(db_user.id)
                water_text = ReportGenerator.format_water_status(water_today, db_user.daily_water_goal_ml)
                keyboard = [[InlineKeyboardButton(text="➕ Вода +250мл", callback_data="water_add_250")], [InlineKeyboardButton(text="📋 Меню", callback_data="open_menu")]]
                await query.edit_message_text(text=f"{report}\n\n{water_text}", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                return

            if data == "menu_week":
                week_data = await self.supabase_service.get_user_nutrition_week(db_user.id)
                user_goals = {
                    'calories': db_user.daily_calories_goal,
                    'protein': db_user.daily_protein_goal,
                    'fats': db_user.daily_fats_goal,
                    'carbs': db_user.daily_carbs_goal
                }
                report = ReportGenerator.format_weekly_report(week_data, user_goals)
                water_week = await self.supabase_service.get_water_week(db_user.id)
                from datetime import date, timedelta
                days = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
                start = date.today() - timedelta(days=6)
                bars = {}
                for i in range(7):
                    d = start + timedelta(days=i)
                    key = d.isoformat()
                    bars[days[i]] = water_week.get(key, 0)
                water_graph = ReportGenerator.format_weekly_water(bars)
                keyboard = [[InlineKeyboardButton(text="📋 Меню", callback_data="open_menu")]]
                await query.edit_message_text(text=f"{report}\n\n{water_graph}", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                return

            if data == "menu_settings_water":
                keyboard = [
                    [InlineKeyboardButton(text="1500мл", callback_data="set_water_1500"), 
                     InlineKeyboardButton(text="2000мл", callback_data="set_water_2000")],
                    [InlineKeyboardButton(text="2500мл", callback_data="set_water_2500"), 
                     InlineKeyboardButton(text="3000мл", callback_data="set_water_3000")],
                    [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="open_menu")]
                ]
                await query.edit_message_text(
                    text="⚙️ *Настройки воды*\n\nВыберите дневную норму:", 
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return

            if data.startswith("set_water_"):
                goal = int(data.split("_")[-1])
                await self.supabase_service.set_user_water_goal(db_user.id, goal)
                keyboard = [[InlineKeyboardButton(text="📋 Меню", callback_data="open_menu")]]
                await query.edit_message_text(
                    text=f"✅ Дневная норма воды установлена: *{goal} мл*", 
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return

            # Обработка подписок - новая система с выбором провайдера
            if data == "choose_monthly":
                await self._show_provider_selection(query, db_user, "monthly")
                return
                
            if data == "choose_yearly":
                await self._show_provider_selection(query, db_user, "yearly")
                return
                
            # Обработка подписок через конкретных провайдеров
            if data.startswith("subscribe_"):
                # Правильный парсинг для telegram_stars который содержит подчеркивания
                parts = data.split("_")
                if len(parts) >= 3:  # subscribe_monthly_provider
                    plan_type = parts[1]
                    provider = "_".join(parts[2:])
                else:
                    return
                
                await self._handle_subscription_request(query, context, db_user, plan_type, provider)
                return

            if data.startswith("crypto_paid_"):
                plan_type = data.split("_")[-1]
                await self._handle_crypto_paid(query, db_user, plan_type)
                return
                
            if data == "subscription_stats":
                await self._show_subscription_stats(query, db_user)
                return
                
            if data == "cancel_subscription":
                await self._handle_subscription_cancellation(query, db_user)
                return
                
            if data == "confirm_cancel_subscription":
                # Отменяем подписку через Stripe
                success = await self.subscription_service.cancel_subscription(db_user.telegram_id)
                if success:
                    message = (
                        f"✅ *Подписка отменена*\n\n"
                        f"Автопродление отключено.\n"
                        f"Подписка останется активной до конца текущего периода."
                    )
                else:
                    message = "❌ Ошибка отмены подписки. Попробуйте позже."
                    
                keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="subscription_stats")]]
                await query.edit_message_text(
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return

        except Exception as e:
            logger.error(f"Ошибка callback_query: {e}")
            try:
                await query.edit_message_text("❌ Произошла ошибка. Попробуйте еще раз.")
            except:
                pass

    async def _show_provider_selection(self, query, db_user, plan_type: str):
        """Показать выбор провайдера для оплаты (только крипто)."""
        try:
            plans = self.subscription_service.get_subscription_plans()
            plan = plans.get(plan_type)
            # Показываем только криптопровайдера
            available_providers = ["crypto"]
            
            if not plan:
                await query.edit_message_text("❌ Неизвестный план подписки")
                return
            
            keyboard = []
            
            # Добавляем кнопку для криптооплаты
            provider = "crypto"
            provider_name = self.subscription_service.get_provider_display_name(provider)
            callback_data = f"subscribe_{plan_type}_{provider}"
            keyboard.append([InlineKeyboardButton(provider_name, callback_data=callback_data)])
            
            # Кнопка назад
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="subscription_stats")])
            
            # Описание провайдера
            provider_descriptions = "• Криптокошелёк — перевод TON или USDT (TRC20)\n"
            
            plan_name = "Месячная" if plan_type == "monthly" else "Годовая"
            
            # Безопасное получение цены с fallback значением
            plan_price = plan.get('price', 4.99 if plan_type == 'monthly' else 49.99)
            plan_currency = plan.get('currency', 'USD')
            plan_duration = plan.get('duration_days', 30 if plan_type == 'monthly' else 365)
            
            message = (
                f"💳 *{plan_name} подписка*\n\n"
                f"💰 Стоимость: ${plan_price} {plan_currency}\n"
                f"📅 Лительность: {plan_duration} дней\n"
                f"📸 Фото: Безлимит\n\n"
                f"💳 *Выберите способ оплаты:*\n\n"
                f"{provider_descriptions}"
            )
            
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка показа выбора провайдера: {e}")
            await query.edit_message_text("❌ Ошибка показа способов оплаты")

    async def _handle_subscription_request(self, query, context: ContextTypes.DEFAULT_TYPE, db_user, plan_type: str, provider: str = None):
        """Обработка запроса на подписку через указанный провайдер"""
        try:
            plans = self.subscription_service.get_subscription_plans()
            plan = plans.get(plan_type)
            
            if not plan:
                await query.edit_message_text("❌ Неизвестный план подписки")
                return
            
            # Определяем провайдер
            if not provider:
                provider = self.subscription_service.primary_provider
            
            # Отправляем сообщение о обработке платежа
            loading_message = await query.edit_message_text("🔄 Обрабатываем запрос на оплату...")
            
            if provider == "crypto":
                crypto_service = self.subscription_service.get_payment_service("crypto")
                instructions = crypto_service.get_payment_instructions(plan_type)
                if not instructions:
                    await query.edit_message_text("❌ Криптокошелёк не настроен. Добавьте адрес в .env")
                    return

                keyboard = [
                    [InlineKeyboardButton("✅ Я оплатил", callback_data=f"crypto_paid_{plan_type}")],
                    [InlineKeyboardButton("🔙 Назад к планам", callback_data="subscription_stats")]
                ]
                await query.edit_message_text(
                    text=instructions,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return
            
            # Прочие провайдеры не поддерживаются
            await query.edit_message_text("❌ Провайдер не поддерживается")
            
        except Exception as e:
            logger.error(f"Ошибка обработки подписки: {e}")
            await query.edit_message_text("❌ Ошибка обработки подписки")

    async def _handle_crypto_paid(self, query, db_user, plan_type: str):
        try:
            crypto_service = self.subscription_service.get_payment_service("crypto")
            # Активируем по подтверждению пользователя (при желании можно запросить TX-хеш отдельно)
            success = await crypto_service.activate_after_user_confirm(db_user.id, plan_type)
            if success:
                keyboard = [
                    [InlineKeyboardButton("📸 Анализировать фото", callback_data="open_menu")],
                    [InlineKeyboardButton("📈 Статистика", callback_data="subscription_stats")],
                ]
                await query.edit_message_text(
                    text=(
                        "✅ Подписка активирована!\n\n"
                        "Спасибо за оплату переводом на криптокошелёк.\n"
                        "Если вы не совершали платеж — напишите в поддержку."
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                return
            await query.edit_message_text("❌ Не удалось активировать подписку. Попробуйте позже.")
        except Exception as e:
            logger.error(f"Crypto paid error: {e}")
            await query.edit_message_text("❌ Ошибка обработки оплаты")
    
    async def _handle_telegram_stars_payment(self, query, context: ContextTypes.DEFAULT_TYPE, db_user, plan_type: str, plan: dict):
        """Обработка оплаты через Telegram Stars"""
        try:
            # Получаем сервис Telegram Stars
            stars_service = self.subscription_service.get_payment_service("telegram_stars")
            if not stars_service:
                await query.edit_message_text("❌ Telegram Stars недоступен")
                return
            
            # Получаем планы из сервиса
            stars_plans = stars_service.get_subscription_plans()
            stars_plan = stars_plans.get(plan_type, {})
            
            if not stars_plan:
                await query.edit_message_text("❌ Неизвестный план Telegram Stars")
                return
            
            # Создаем инвойс напрямую через bot API
            from telegram import LabeledPrice
            
            # Безопасное получение данных для инвойса
            stars_name = stars_plan.get('name', 'Подписка Telegram Stars')
            stars_price = stars_plan.get('price_stars', 100 if plan_type == 'monthly' else 1000)
            stars_duration = stars_plan.get('duration_days', 30 if plan_type == 'monthly' else 365)
            
            prices = [LabeledPrice(
                label=stars_name,
                amount=stars_price
            )]
            
            payload = f"stars_subscription_{db_user.id}_{plan_type}_{int(datetime.now().timestamp())}"
            
            # Отправляем инвойс напрямую
            await context.bot.send_invoice(
                chat_id=query.message.chat_id,
                title=f"⭐ {stars_name}",
                description=f"Безлимитный анализ фото еды на {stars_duration} дней\n"
                           f"💰 Цена: {stars_price} Telegram Stars\n"
                           f"📸 Неограниченное количество фото\n"
                           f"🤖 ИИ анализ калорий, белков, жиров, углеводов",
                payload=payload,
                provider_token="",  # Пустой для Telegram Stars
                currency="XTR",     # XTR = Telegram Stars
                prices=prices,
                start_parameter=f"stars_subscription_{plan_type}",
                photo_url="https://telegram.org/img/t_logo.png",
                photo_size=512,
                photo_width=512,
                photo_height=512,
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                send_phone_number_to_provider=False,
                send_email_to_provider=False,
                is_flexible=False
            )
            
            # Обновляем сообщение с информацией об оплате
            keyboard = [
                [InlineKeyboardButton("🔙 Назад к планам", callback_data="subscription_stats")]
            ]
            
            # Безопасное получение данных Telegram Stars плана
            stars_name = stars_plan.get('name', 'Подписка Telegram Stars')
            stars_price = stars_plan.get('price_stars', 100 if plan_type == 'monthly' else 1000)
            stars_duration = stars_plan.get('duration_days', 30 if plan_type == 'monthly' else 365)
            
            message = (
                f"⭐ *{stars_name} - Telegram Stars*\n\n"
                f"💰 Стоимость: {stars_price} ⭐ Stars\n"
                f"📅 Длительность: {stars_duration} дней\n"
                f"📸 Фото: Безлимит\n\n"
                f"ℹ️ *Оплата через Telegram Stars:*\n"
                f"1. Инвойс отправлен в чат\n"
                f"2. Нажмите кнопку 'Оплатить' в инвойсе\n"
                f"3. Подтвердите оплату Stars\n"
                f"4. Подписка активируется автоматически!\n\n"
                f"⭐ *Telegram Stars:* Внутренняя валюта Telegram\n"
                f"🔄 *Подписка:* Продлевается автоматически каждые {stars_duration} дней"
            )
            
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
            logger.info(f"Создан Telegram Stars инвойс для пользователя {db_user.id}: {plan_type}")
            
        except Exception as e:
            logger.error(f"Ошибка обработки Telegram Stars: {e}")
            await query.edit_message_text("❌ Ошибка обработки оплаты")
    
    async def handle_pre_checkout_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка предварительного запроса оплаты Telegram Stars и Telegram Payments"""
        try:
            query = update.pre_checkout_query

            payload = query.invoice_payload or ""

            if payload.startswith("stars_"):
                stars_service = self.subscription_service.get_payment_service("telegram_stars")
                if not stars_service:
                    await query.answer(ok=False, error_message="Ошибка: Telegram Stars недоступен")
                    return
                is_valid = await stars_service.handle_pre_checkout_query(query)
                if is_valid:
                    await query.answer(ok=True)
                    logger.info(f"Предварительная проверка прошла успешно: {query.id}")
                else:
                    await query.answer(ok=False, error_message="Ошибка проверки платежа")
                    logger.error(f"Ошибка предварительной проверки: {query.id}")
                return

            if payload.startswith("tgpay_"):
                tgpay_service = self.subscription_service.get_payment_service("telegram_payments")
                if not tgpay_service:
                    await query.answer(ok=False, error_message="Ошибка: Telegram Payments недоступен")
                    return
                result = await tgpay_service.handle_pre_checkout(payload, query.total_amount, query.currency)
                if result:
                    await query.answer(ok=True)
                    logger.info(f"Pre-checkout OK (Telegram Payments): {query.id}")
                else:
                    await query.answer(ok=False, error_message="Ошибка проверки платежа")
                    logger.error(f"Pre-checkout failed (Telegram Payments): {query.id}")
                return

            await query.answer(ok=False, error_message="Неизвестный тип платежа")
                
        except Exception as e:
            logger.error(f"Ошибка обработки предварительного запроса: {e}")
            try:
                await update.pre_checkout_query.answer(ok=False, error_message="Ошибка обработки")
            except:
                pass
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка успешной оплаты Telegram Stars и Telegram Payments"""
        try:
            payment = update.message.successful_payment
            user = update.effective_user
            
            logger.info(f"Получена успешная оплата: {payment.telegram_payment_charge_id}")
            
            # Получаем пользователя из БД
            db_user = await self.supabase_service.get_user_by_telegram_id(user.id)
            if not db_user:
                logger.error(f"Пользователь {user.id} не найден в БД")
                await update.message.reply_text("❌ Ошибка: пользователь не найден")
                return
            
            payload = payment.invoice_payload or ""

            # Telegram Payments success
            if payload.startswith("tgpay_"):
                tgpay_service = self.subscription_service.get_payment_service("telegram_payments")
                if not tgpay_service:
                    logger.error("Telegram Payments сервис недоступен")
                    await update.message.reply_text("❌ Ошибка обработки платежа")
                    return
                activated = await tgpay_service.activate_after_success(
                    payload=payload,
                    telegram_payment_charge_id=payment.telegram_payment_charge_id,
                    provider_payment_charge_id=payment.provider_payment_charge_id,
                )
                if activated:
                    keyboard = [
                        [InlineKeyboardButton("📸 Анализировать фото", callback_data="open_menu")],
                        [InlineKeyboardButton("📈 Статистика", callback_data="subscription_stats")],
                    ]
                    await update.message.reply_text(
                        "✅ *Подписка активирована!*\n\n"
                        f"💳 Оплата через {getattr(settings, 'PAYMENT_PROVIDER_NAME', 'Telegram Payments')}\n"
                        "📸 Теперь вы можете анализировать неограниченное количество фото!\n\n"
                        "🔄 Подписка продлевается автоматически\n"
                        "❌ Отменить можно в любое время",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                    logger.info(f"Подписка активирована (Telegram Payments) для пользователя {user.id}")
                else:
                    await update.message.reply_text("❌ Ошибка активации подписки. Обратитесь в поддержку.")
                    logger.error(f"Ошибка активации подписки (Telegram Payments) для пользователя {user.id}")
                return

            # Telegram Stars success
            if payload.startswith("stars_"):
                stars_service = self.subscription_service.get_payment_service("telegram_stars")
                if not stars_service:
                    logger.error("Telegram Stars сервис недоступен")
                    await update.message.reply_text("❌ Ошибка обработки платежа")
                    return
                success = await stars_service.handle_successful_payment(update=update, context=context)
                if success:
                    # Отправляем подтверждение
                    keyboard = [
                        [InlineKeyboardButton("📸 Анализировать фото", callback_data="open_menu")],
                        [InlineKeyboardButton("📈 Статистика", callback_data="subscription_stats")]
                    ]
                    
                    await update.message.reply_text(
                        f"✅ *Подписка активирована!*\n\n"
                        f"⭐ Оплата через Telegram Stars: {payment.total_amount} Stars\n"
                        f"📸 Теперь вы можете анализировать неограниченное количество фото!\n\n"
                        f"🔄 Подписка продлевается автоматически\n"
                        f"❌ Отменить можно в любое время",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    logger.info(f"Подписка успешно активирована для пользователя {user.id}")
                else:
                    await update.message.reply_text("❌ Ошибка активации подписки. Обратитесь в поддержку.")
                    logger.error(f"Ошибка активации подписки для пользователя {user.id}")
                return

            await update.message.reply_text("❌ Неизвестный тип платежа")
                
        except Exception as e:
            logger.error(f"Ошибка обработки успешной оплаты: {e}")
            try:
                await update.message.reply_text("❌ Ошибка обработки платежа")
            except:
                pass

    async def _show_subscription_stats(self, query, db_user):
        """Показать статистику подписки"""
        try:
            # Получаем информацию о подписке
            subscription_info = await self.subscription_service.get_user_subscription(db_user.telegram_id)
            
            if not subscription_info:
                await query.edit_message_text("❌ Ошибка получения информации о подписке")
                return
            
            status = subscription_info.get("status", "free")
            plan = subscription_info.get("plan")
            photos_analyzed = subscription_info.get("photos_analyzed", 0)
            subscription_end = subscription_info.get("current_period_end") or subscription_info.get("subscription_end")
            
            # Формируем сообщение в зависимости от статуса
            if status == "active":
                status_emoji = "✅"
                status_text = "Активная"
                plan_text = f"\n📜 План: {plan.title() if plan else 'Неизвестно'}"
                
                if subscription_end:
                    from datetime import datetime
                    if isinstance(subscription_end, str):
                        end_date = datetime.fromisoformat(subscription_end.replace('Z', '+00:00'))
                    else:
                        end_date = subscription_end
                    end_text = f"\n📅 Окончание: {end_date.strftime('%d.%m.%Y')}"
                else:
                    end_text = ""
                    
                photos_text = f"\n📸 Проанализировано: {photos_analyzed} (безлимит)"
                
                keyboard = [
                    [InlineKeyboardButton("❌ Отменить подписку", callback_data="cancel_subscription")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="show_subscription_plans")]
                ]
                
            elif status == "expired":
                status_emoji = "⚠️"
                status_text = "Истекла"
                plan_text = f"\n📜 План: {plan.title() if plan else 'Нет'}"
                end_text = ""
                photos_text = f"\n📸 Проанализировано: {photos_analyzed}/1 (бесплатно)"
                
                keyboard = [
                    [InlineKeyboardButton("💳 Продлить подписку", callback_data="show_subscription_plans")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="show_subscription_plans")]
                ]
                
            else:  # free
                status_emoji = "🆓"
                status_text = "Бесплатная"
                plan_text = ""
                end_text = ""
                photos_text = f"\n📸 Проанализировано: {photos_analyzed}/1 (бесплатно)"
                
                keyboard = [
                    [InlineKeyboardButton("💳 Оформить подписку", callback_data="show_subscription_plans")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="show_subscription_plans")]
                ]
            
            message = (
                f"📊 *Статистика подписки*\n\n"
                f"{status_emoji} Статус: {status_text}{plan_text}{end_text}{photos_text}\n\n"
                f"ℹ️ *О подписке:*\n"
                f"• Первое фото - бесплатно\n"
                f"• Подписка - безлимит фото\n"
                f"• Автопродление\n"
                f"• Отмена в любое время"
            )
            
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка показа статистики подписки: {e}")
            await query.edit_message_text("❌ Ошибка получения статистики")

    async def _handle_subscription_cancellation(self, query, db_user):
        """Обработка отмены подписки"""
        try:
            # Подтверждение отмены
            keyboard = [
                [InlineKeyboardButton("✅ Да, отменить", callback_data="confirm_cancel_subscription")],
                [InlineKeyboardButton("❌ Нет, оставить", callback_data="subscription_stats")]
            ]
            
            message = (
                f"⚠️ *Отмена подписки*\n\n"
                f"Вы уверены, что хотите отменить подписку?\n\n"
                f"ℹ️ *Что произойдет:*\n"
                f"• Подписка останется активной до конца текущего периода\n"
                f"• Автопродление будет отключено\n"
                f"• После истечения вернется бесплатный режим (1 фото)"
            )
            
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки отмены подписки: {e}")
            await query.edit_message_text("❌ Ошибка обработки отмены")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats - показать статистику за день"""
        try:
            user = update.effective_user
            
            # Получаем пользователя из БД
            db_user = await self.supabase_service.get_user_by_telegram_id(user.id)
            if not db_user:
                await update.message.reply_text("❌ Пользователь не найден. Используйте /start для регистрации.")
                return
            
            # Отправляем сообщение о начале обработки
            processing_msg = await update.message.reply_text("📊 Загружаю статистику за сегодня...")
            
            # Получаем данные о питании за сегодня
            nutrition_data = await self.supabase_service.get_user_nutrition_today(db_user.id)
            
            # Формируем цели пользователя
            user_goals = {
                'calories': db_user.daily_calories_goal,
                'protein': db_user.daily_protein_goal,
                'fats': db_user.daily_fats_goal,
                'carbs': db_user.daily_carbs_goal
            }
            
            # Генерируем отчет
            report = ReportGenerator.format_daily_report(nutrition_data, user_goals)
            
            # Вода за сегодня
            water_today = await self.supabase_service.get_water_today(db_user.id)
            water_text = ReportGenerator.format_water_status(water_today, db_user.daily_water_goal_ml)
            keyboard = [
                [InlineKeyboardButton(text="➕ Вода +250мл", callback_data="water_add_250")],
                [InlineKeyboardButton(text="📋 Меню", callback_data="open_menu")]
            ]
            # Удаляем сообщение о загрузке и отправляем отчет
            await processing_msg.delete()
            await update.message.reply_text(f"{report}\n\n{water_text}", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            
        except Exception as e:
            logger.error(f"Ошибка в команде stats: {e}")
            await update.message.reply_text("❌ Произошла ошибка при загрузке статистики. Попробуйте позже.")
    
    async def week_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /week - показать статистику за неделю"""
        try:
            user = update.effective_user
            
            # Получаем пользователя из БД
            db_user = await self.supabase_service.get_user_by_telegram_id(user.id)
            if not db_user:
                await update.message.reply_text("❌ Пользователь не найден. Используйте /start для регистрации.")
                return
            
            # Отправляем сообщение о начале обработки
            processing_msg = await update.message.reply_text("📈 Загружаю статистику за неделю...")
            
            # Получаем данные о питании за неделю
            week_data = await self.supabase_service.get_user_nutrition_week(db_user.id)
            
            # Формируем цели пользователя
            user_goals = {
                'calories': db_user.daily_calories_goal,
                'protein': db_user.daily_protein_goal,
                'fats': db_user.daily_fats_goal,
                'carbs': db_user.daily_carbs_goal
            }
            
            # Генерируем отчет
            report = ReportGenerator.format_weekly_report(week_data, user_goals)
            
            # Вода по дням недели
            water_week = await self.supabase_service.get_water_week(db_user.id)
            # Преобразуем в дни Пн..Вс
            from datetime import date, timedelta
            days = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
            start = date.today() - timedelta(days=6)
            bars = {}
            for i in range(7):
                d = start + timedelta(days=i)
                key = d.isoformat()
                bars[days[i]] = water_week.get(key, 0)
            water_graph = ReportGenerator.format_weekly_water(bars)
            keyboard = [[InlineKeyboardButton(text="📋 Меню", callback_data="open_menu")]]
            # Удаляем сообщение о загрузке и отправляем отчет
            await processing_msg.delete()
            await update.message.reply_text(f"{report}\n\n{water_graph}", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            
        except Exception as e:
            logger.error(f"Ошибка в команде week: {e}")
            await update.message.reply_text("❌ Произошла ошибка при загрузке статистики. Попробуйте позже.")
