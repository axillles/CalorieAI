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
        """Photo processor"""
        try:
            user = update.effective_user
            
            # Получаем пользователя из БД
            db_user = await self.supabase_service.get_user_by_telegram_id(user.id)
            if not db_user:
                await update.message.reply_text("❌ User not found. Please use /start to register.")
                return
            
            # Проверяем подписку перед анализом
            subscription_check = await self.subscription_service.can_analyze_photo(user.id)
            
            if not subscription_check["can_analyze"]:
                if subscription_check["reason"] == "subscription_required":
                    # Показываем планы подписки с выбором провайдера
                    plans = subscription_check["subscription_plans"]
                    available_providers = ["crypto"]
                    
                    keyboard = []
                    
                    # Короткие кнопки для планов
                    keyboard.append([InlineKeyboardButton("💳 Monthly subscription", callback_data="choose_monthly")])
                    keyboard.append([InlineKeyboardButton("💰 Annual subscription", callback_data="choose_yearly")])
                    keyboard.append([InlineKeyboardButton("📊 Usage statistics", callback_data="subscription_stats")])
                    
                    # Безопасное получение цен с fallback значениями
                    monthly_price = plans.get('monthly', {}).get('price', 4.99)
                    yearly_price = plans.get('yearly', {}).get('price', 49.99)
                    
                    message = (
                        f"⚠️ *The limit of free photos has been reached!*\n\n"
                        f"You have analyzed: {subscription_check['photos_analyzed']} фото\n\n"
                        f"💡 *Select a subscription plan:*\n\n"
                        f"💳 **Monthly:** ${monthly_price} - unlimited photo\n"
                        f"💰 **Annual:** ${yearly_price} - unlimited photos (save 17%)\n\n"
                        f"💳 *Available payment methods:*\n"
                    )
                    
                    for provider in available_providers:
                        provider_name = self.subscription_service.get_provider_display_name(provider)
                        if provider == "crypto":
                            message += f"• {provider_name} - transaction TON or USDT (TRC20)\n"
                    
                    message += f"\nAfter payment you will be able to analyze an unlimited number of photos!"
                    
                    await update.message.reply_text(message, parse_mode='Markdown', 
                                                 reply_markup=InlineKeyboardMarkup(keyboard))
                    return
                else:
                    await update.message.reply_text("❌ Error checking subscription. Try again later.")
                    return
            
            # Send processing message (English)
            processing_msg = await update.message.reply_text("🔍 Analyzing image...")
            
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
            
            # Увеличиваем счетчик общих отправленных фото
            await self.supabase_service.increment_total_photos_sent(user.id)
            
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
                    'weight_grams': nutrition_analysis.weight_grams
                })
                
                # Buttons after analysis
                tg_weight = int(nutrition_analysis.weight_grams) if nutrition_analysis.weight_grams else 200
                keyboard = [
                    [InlineKeyboardButton(text="➕ Water +250ml", callback_data="water_add_250")],
                    [InlineKeyboardButton(text=f"⚖️ Change weight ({tg_weight} g)", callback_data=f"change_weight_{created_image.id}_{tg_weight}")],
                    [InlineKeyboardButton(text="📋 Menu", callback_data="open_menu")]
                ]
                # Увеличиваем счетчик проанализированных фото
                await self.subscription_service.increment_photos_analyzed(user.id)
                
                # Удаляем сообщение о загрузке и отправляем результат
                await processing_msg.delete()
                await update.message.reply_text(result_message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                
            except OpenAIQuotaError:
                logger.error("Analysis stopped: OpenAI quota exceeded")
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
                            [InlineKeyboardButton(text="➕ Water +250ml", callback_data="water_add_250")],
                            [InlineKeyboardButton(text="📋 Menu", callback_data="open_menu")]
                        ]
                        await processing_msg.delete()
                        await update.message.reply_text(result_message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                        return
                await self.supabase_service.update_food_image_status(created_image.id, "error")
                await processing_msg.delete()
                await update.message.reply_text("⚠️ OpenAI quota exceeded. Try again later or check API billing.")
            except Exception as e:
                logger.error(f"Image analysis error: {e}")
                await self.supabase_service.update_food_image_status(created_image.id, "error")
                await processing_msg.delete()
                await update.message.reply_text("❌ Image analysis error. Please try again.")
                
        except Exception as e:
            logger.error(f"Photo handling error: {e}")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text="📋 Menu", callback_data="open_menu")]
            ])
            await update.message.reply_text(
                "❌ An error occurred. Please try again later.",
                reply_markup=keyboard
            )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            text = update.message.text
            
            if text.startswith('/'):
                # Команды обрабатываются в command_handler
                return
            
            # Handle weight input if awaiting
            awaiting_image_id = context.user_data.get("awaiting_weight_for_image")
            if awaiting_image_id is not None:
                try:
                    new_weight = int(''.join(ch for ch in text if ch.isdigit()))
                    if new_weight <= 0:
                        raise ValueError
                    nd = self.supabase_service.supabase.table("nutrition_data").select("id, calories, protein, fats, carbs, weight_grams").eq("food_image_id", awaiting_image_id).order("created_at", desc=True).limit(1).execute()
                    if nd.data:
                        row = nd.data[0]
                        old_w = row.get("weight_grams") or new_weight
                        factor = new_weight / old_w if old_w else 1
                        updated = {
                            "calories": round(row["calories"] * factor, 1),
                            "protein": round(row["protein"] * factor, 1),
                            "fats": round(row["fats"] * factor, 1),
                            "carbs": round(row["carbs"] * factor, 1),
                            "weight_grams": new_weight,
                        }
                        self.supabase_service.supabase.table("nutrition_data").update(updated).eq("id", row["id"]).execute()
                        img = self.supabase_service.supabase.table("food_images").select("user_id").eq("id", awaiting_image_id).single().execute()
                        user_id = img.data["user_id"] if img and img.data else None
                        if user_id:
                            await self._update_daily_report(user_id)
                        # Показываем обновленный экран с результатами анализа
                        await self._show_nutrition_analysis_screen(update, awaiting_image_id, new_weight)
                    else:
                        await update.message.reply_text(
                            "❌ Could not find analysis for this image.",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="📋 Menu", callback_data="open_menu")]])
                        )
                except Exception:
                    # Показываем экран анализа с текущим весом при ошибке ввода
                    await self._show_nutrition_analysis_screen(update, awaiting_image_id)
                finally:
                    context.user_data.pop("awaiting_weight_for_image", None)
                return
            
            # If not a command, send a hint (English)
            await update.message.reply_text(
                "📸 Send a photo of your meal to analyze nutrition!\n\n"
                "Or use commands:\n"
                "/stats - today stats\n"
                "/week - weekly stats\n"
                "/help - help"
            )
            
        except Exception as e:
            logger.error(f"Text handling error: {e}")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text="📋 Menu", callback_data="open_menu")]
            ])
            await update.message.reply_text(
                "❌ An error occurred. Please try again later.",
                reply_markup=keyboard
            )
    
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

    async def _show_nutrition_analysis_screen(self, update: Update, image_id: int, weight_grams: int = None):
        """Показывает экран с результатами анализа питания"""
        try:
            # Получаем данные анализа из базы
            nd = self.supabase_service.supabase.table("nutrition_data").select("id, calories, protein, fats, carbs, weight_grams, food_name, confidence").eq("food_image_id", image_id).order("created_at", desc=True).limit(1).execute()
            
            if not nd.data:
                await update.message.reply_text("❌ Could not find analysis data.")
                return
            
            row = nd.data[0]
            current_weight = weight_grams if weight_grams is not None else row.get("weight_grams", 200)
            
            # Форматируем результат с актуальным весом
            result_message = ReportGenerator.format_nutrition_result({
                'food_name': row.get('food_name', 'unknown'),
                'calories': row['calories'],
                'protein': row['protein'],
                'fats': row['fats'],
                'carbs': row['carbs'],
                'weight_grams': current_weight,
                'confidence': row.get('confidence', 0.8)
            })
            
            # Создаем клавиатуру с кнопкой изменения веса
            keyboard = [
                [InlineKeyboardButton(text="➕ Water +250ml", callback_data="water_add_250")],
                [InlineKeyboardButton(text=f"⚖️ Change weight ({current_weight} g)", callback_data=f"change_weight_{image_id}_{current_weight}")],
                [InlineKeyboardButton(text="📋 Menu", callback_data="open_menu")]
            ]
            
            # Отправляем или редактируем сообщение
            if hasattr(update, 'edit_message_text'):
                await update.edit_message_text(
                    text=result_message, 
                    parse_mode='Markdown', 
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(
                    result_message, 
                    parse_mode='Markdown', 
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Error showing nutrition analysis screen: {e}")
            await update.message.reply_text("❌ Error displaying analysis results.")
