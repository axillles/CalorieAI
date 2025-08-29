from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from services.supabase_service import SupabaseService
from services.openai_service import OpenAIService, OpenAIQuotaError
from services.g4f_service import G4FService
from services.subscription_service import SubscriptionService
from config.settings import settings
from utils.report_generator import ReportGenerator
from models.data_models import User, FoodImage, NutritionData, DailyReport
from datetime import datetime, date
import logging
import os

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.openai_service = OpenAIService()
        self.g4f_service = G4FService() if settings.ENABLE_G4F_FALLBACK else None
        self.subscription_service = SubscriptionService()
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        try:
            user = update.effective_user
            
            # Получаем пользователя из БД
            db_user = await self.supabase_service.get_user_by_telegram_id(user.id)
            if not db_user:
                await update.message.reply_text("❌ Пользователь не найден. Используйте /start для регистрации.")
                return
            
            # Проверяем подписку перед анализом
            subscription_check = await self.subscription_service.can_analyze_photo(db_user.id)
            
            if not subscription_check["can_analyze"]:
                if subscription_check["reason"] == "subscription_required":
                    # Показываем планы подписки
                    plans = subscription_check["subscription_plans"]
                    keyboard = [
                        [InlineKeyboardButton(f"💳 {plans['monthly']['name']} - ${plans['monthly']['price']}", 
                                            callback_data="subscribe_monthly")],
                        [InlineKeyboardButton(f"💳 {plans['yearly']['name']} - ${plans['yearly']['price']}", 
                                            callback_data="subscribe_yearly")],
                        [InlineKeyboardButton("📊 Статистика использования", callback_data="subscription_stats")]
                    ]
                    
                    message = (
                        f"⚠️ *Лимит бесплатных фото исчерпан!*\n\n"
                        f"Вы проанализировали: {subscription_check['photos_analyzed']} фото\n\n"
                        f"💡 *Выберите план подписки:*\n"
                        f"• Месячная: ${plans['monthly']['price']} - безлимит фото\n"
                        f"• Годовая: ${plans['yearly']['price']} - безлимит фото (экономия 17%)\n\n"
                        f"После оплаты вы сможете анализировать неограниченное количество фото!"
                    )
                    
                    await update.message.reply_text(message, parse_mode='Markdown', 
                                                 reply_markup=InlineKeyboardMarkup(keyboard))
                    return
                else:
                    await update.message.reply_text("❌ Ошибка проверки подписки. Попробуйте позже.")
                    return
            
            # Отправляем сообщение о начале обработки
            processing_msg = await update.message.reply_text("🔍 Анализирую изображение...")
            
            # Получаем фотографию
            photo = update.message.photo[-1]  # Берем самое большое изображение
            
            # Скачиваем изображение
            file = await context.bot.get_file(photo.file_id)
            image_bytes = await file.download_as_bytearray()
            
            # Сохраняем изображение в Supabase Storage (опционально)
            # Для простоты пока сохраняем URL файла
            image_url = file.file_path
            
            # Создаем запись о фотографии
            food_image = FoodImage(
                user_id=db_user.id,
                image_url=image_url,
                status="processing"
            )
            created_image = await self.supabase_service.create_food_image(food_image)
            
            try:
                # Анализируем изображение через OpenAI
                nutrition_analysis = self.openai_service.analyze_food_image(image_bytes)
                
                # Создаем запись о питательных веществах
                nutrition_data = NutritionData(
                    food_image_id=created_image.id,
                    calories=nutrition_analysis.calories,
                    protein=nutrition_analysis.protein,
                    fats=nutrition_analysis.fats,
                    carbs=nutrition_analysis.carbs,
                    food_name=nutrition_analysis.food_name,
                    confidence=nutrition_analysis.confidence
                )
                
                await self.supabase_service.create_nutrition_data(nutrition_data)
                
                # Обновляем статус фотографии
                await self.supabase_service.update_food_image_status(created_image.id, "processed")
                
                # Обновляем дневной отчет
                await self._update_daily_report(db_user.id)
                
                # Форматируем результат
                result_message = ReportGenerator.format_nutrition_result({
                    'food_name': nutrition_analysis.food_name,
                    'calories': nutrition_analysis.calories,
                    'protein': nutrition_analysis.protein,
                    'fats': nutrition_analysis.fats,
                    'carbs': nutrition_analysis.carbs,
                    'confidence': nutrition_analysis.confidence
                })
                
                # Кнопки после анализа
                keyboard = [
                    [InlineKeyboardButton(text="➕ Вода +250мл", callback_data="water_add_250")],
                    [InlineKeyboardButton(text="📋 Меню", callback_data="open_menu")]
                ]
                # Увеличиваем счетчик проанализированных фото
                await self.subscription_service.increment_photos_analyzed(db_user.id)
                
                # Удаляем сообщение о загрузке и отправляем результат
                await processing_msg.delete()
                await update.message.reply_text(result_message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                
            except OpenAIQuotaError:
                logger.error("Анализ прерван: исчерпана квота OpenAI")
                # Если включен фолбэк g4f — пробуем анализ по URL
                if self.g4f_service:
                    fallback_result = self.g4f_service.analyze_food_image_url(image_url)
                    if fallback_result:
                        nutrition_data = NutritionData(
                            food_image_id=created_image.id,
                            calories=fallback_result.calories,
                            protein=fallback_result.protein,
                            fats=fallback_result.fats,
                            carbs=fallback_result.carbs,
                            food_name=fallback_result.food_name,
                            confidence=fallback_result.confidence
                        )
                        await self.supabase_service.create_nutrition_data(nutrition_data)
                        await self.supabase_service.update_food_image_status(created_image.id, "processed")
                        await self._update_daily_report(db_user.id)
                        result_message = ReportGenerator.format_nutrition_result({
                            'food_name': fallback_result.food_name,
                            'calories': fallback_result.calories,
                            'protein': fallback_result.protein,
                            'fats': fallback_result.fats,
                            'carbs': fallback_result.carbs,
                            'confidence': fallback_result.confidence
                        })
                        keyboard = [
                            [InlineKeyboardButton(text="➕ Вода +250мл", callback_data="water_add_250")],
                            [InlineKeyboardButton(text="📋 Меню", callback_data="open_menu")]
                        ]
                        await processing_msg.delete()
                        await update.message.reply_text(result_message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                        return
                await self.supabase_service.update_food_image_status(created_image.id, "error")
                await processing_msg.delete()
                await update.message.reply_text("⚠️ Превышена квота OpenAI. Попробуйте позже или проверьте биллинг API.")
            except Exception as e:
                logger.error(f"Ошибка анализа изображения: {e}")
                await self.supabase_service.update_food_image_status(created_image.id, "error")
                await processing_msg.delete()
                await update.message.reply_text("❌ Ошибка при анализе изображения. Попробуйте еще раз.")
                
        except Exception as e:
            logger.error(f"Ошибка обработки фотографии: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            text = update.message.text
            
            if text.startswith('/'):
                # Команды обрабатываются в command_handler
                return
            
            # Если это не команда, отправляем подсказку
            await update.message.reply_text(
                "📸 Отправьте мне фотографию еды для анализа КБЖУ!\n\n"
                "Или используйте команды:\n"
                "/stats - статистика за день\n"
                "/week - статистика за неделю\n"
                "/help - справка"
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки текстового сообщения: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
    
    async def _update_daily_report(self, user_id: int):
        """Обновить дневной отчет пользователя"""
        try:
            # Получаем данные о питании за сегодня
            nutrition_data = await self.supabase_service.get_user_nutrition_today(user_id)
            
            # Создаем или обновляем дневной отчет
            daily_report = DailyReport(
                user_id=user_id,
                date=date.today(),
                total_calories=nutrition_data['calories'],
                total_protein=nutrition_data['protein'],
                total_fats=nutrition_data['fats'],
                total_carbs=nutrition_data['carbs']
            )
            
            await self.supabase_service.create_or_update_daily_report(daily_report)
            
        except Exception as e:
            logger.error(f"Ошибка обновления дневного отчета: {e}")
