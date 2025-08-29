from telegram import Update
from telegram.ext import ContextTypes
from services.supabase_service import SupabaseService
from services.subscription_service import SubscriptionService
from utils.report_generator import ReportGenerator
from models.data_models import User
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
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

            # Обработка подписок
            if data == "subscribe_monthly":
                await self._handle_subscription_request(query, db_user, "monthly")
                return
                
            if data == "subscribe_yearly":
                await self._handle_subscription_request(query, db_user, "yearly")
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

    async def _handle_subscription_request(self, query, db_user, plan_type: str):
        """Обработка запроса на подписку через Stripe"""
        try:
            plans = self.subscription_service.get_subscription_plans()
            plan = plans.get(plan_type)
            
            if not plan:
                await query.edit_message_text("❌ Неизвестный план подписки")
                return
            
            # Отправляем сообщение о создании ссылки
            loading_message = await query.edit_message_text("🔄 Создаем ссылку на оплату...")
            
            # Создаем Stripe Checkout Session
            payment_url = await self.subscription_service.create_payment_link(
                user_id=db_user.id,
                plan_type=plan_type,
                telegram_user_id=query.from_user.id
            )
            
            if not payment_url:
                await query.edit_message_text("❌ Ошибка создания ссылки на оплату. Попробуйте позже.")
                return
            
            # Создаем клавиатуру со ссылкой на оплату
            keyboard = [
                [InlineKeyboardButton("💳 Оплатить через Stripe", url=payment_url)],
                [InlineKeyboardButton("🔙 Назад к планам", callback_data="show_subscription_plans")]
            ]
            
            message = (
                f"💳 *{plan['name']}*\n\n"
                f"💰 Стоимость: ${plan['price']} {plan['currency']}\n"
                f"📅 Длительность: {plan['duration_days']} дней\n"
                f"📸 Фото: Безлимит\n\n"
                f"ℹ️ *Как оплатить:*\n"
                f"1. Нажмите кнопку 'Оплатить через Stripe'\n"
                f"2. Введите данные карты\n"
                f"3. Подтвердите оплату\n"
                f"4. Подписка активируется автоматически!\n\n"
                f"🔒 *Безопасность:* Оплата обрабатывается Stripe\n"
                f"🔄 *Подписка:* Продлевается автоматически каждые {plan['duration_days']} дней\n"
                f"❌ *Отмена:* Можно отменить в любое время"
            )
            
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки подписки: {e}")
            await query.edit_message_text("❌ Ошибка обработки подписки")

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
                f"• Автопродление через Stripe\n"
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
