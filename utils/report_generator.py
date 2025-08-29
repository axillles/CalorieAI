from datetime import datetime, date
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    @staticmethod
    def format_daily_report(nutrition_data: Dict[str, float], user_goals: Dict[str, int] = None) -> str:
        """Форматировать дневной отчет"""
        try:
            calories = nutrition_data.get('calories', 0)
            protein = nutrition_data.get('protein', 0)
            fats = nutrition_data.get('fats', 0)
            carbs = nutrition_data.get('carbs', 0)
            
            # Используем дефолтные цели если не переданы
            if not user_goals:
                user_goals = {
                    'calories': 2000,
                    'protein': 150,
                    'fats': 65,
                    'carbs': 250
                }
            
            # Рассчитываем проценты от дневной нормы
            calories_percent = min((calories / user_goals['calories']) * 100, 100)
            protein_percent = min((protein / user_goals['protein']) * 100, 100)
            fats_percent = min((fats / user_goals['fats']) * 100, 100)
            carbs_percent = min((carbs / user_goals['carbs']) * 100, 100)
            
            # Создаем прогресс-бары
            calories_bar = ReportGenerator._create_progress_bar(calories_percent)
            protein_bar = ReportGenerator._create_progress_bar(protein_percent)
            fats_bar = ReportGenerator._create_progress_bar(fats_percent)
            carbs_bar = ReportGenerator._create_progress_bar(carbs_percent)
            
            report = f"""
📊 *Дневной отчет питания*

🍽️ **Калории:** {calories:.0f} / {user_goals['calories']} ккал ({calories_percent:.1f}%)
{calories_bar}

🥩 **Белки:** {protein:.1f} / {user_goals['protein']}г ({protein_percent:.1f}%)
{protein_bar}

🧈 **Жиры:** {fats:.1f} / {user_goals['fats']}г ({fats_percent:.1f}%)
{fats_bar}

🍞 **Углеводы:** {carbs:.1f} / {user_goals['carbs']}г ({carbs_percent:.1f}%)
{carbs_bar}

📅 Дата: {date.today().strftime('%d.%m.%Y')}
"""
            return report.strip()
            
        except Exception as e:
            logger.error(f"Ошибка форматирования дневного отчета: {e}")
            return "❌ Ошибка генерации отчета"
    
    @staticmethod
    def format_weekly_report(week_data: Dict[str, float], user_goals: Dict[str, int] = None) -> str:
        """Форматировать недельный отчет"""
        try:
            total_calories = week_data.get('total_calories', 0)
            total_protein = week_data.get('total_protein', 0)
            total_fats = week_data.get('total_fats', 0)
            total_carbs = week_data.get('total_carbs', 0)
            
            avg_calories = week_data.get('average_calories', 0)
            avg_protein = week_data.get('average_protein', 0)
            avg_fats = week_data.get('average_fats', 0)
            avg_carbs = week_data.get('average_carbs', 0)
            
            # Используем дефолтные цели если не переданы
            if not user_goals:
                user_goals = {
                    'calories': 2000,
                    'protein': 150,
                    'fats': 65,
                    'carbs': 250
                }
            
            # Рассчитываем средние проценты от дневной нормы
            avg_calories_percent = min((avg_calories / user_goals['calories']) * 100, 100)
            avg_protein_percent = min((avg_protein / user_goals['protein']) * 100, 100)
            avg_fats_percent = min((avg_fats / user_goals['fats']) * 100, 100)
            avg_carbs_percent = min((avg_carbs / user_goals['carbs']) * 100, 100)
            
            # Создаем прогресс-бары для средних значений
            avg_calories_bar = ReportGenerator._create_progress_bar(avg_calories_percent)
            avg_protein_bar = ReportGenerator._create_progress_bar(avg_protein_percent)
            avg_fats_bar = ReportGenerator._create_progress_bar(avg_fats_percent)
            avg_carbs_bar = ReportGenerator._create_progress_bar(avg_carbs_percent)
            
            report = f"""
📈 *Недельный отчет питания*

📊 **Общие показатели за неделю:**
🍽️ Калории: {total_calories:.0f} ккал
🥩 Белки: {total_protein:.1f}г
🧈 Жиры: {total_fats:.1f}г
🍞 Углеводы: {total_carbs:.1f}г

📅 **Средние показатели в день:**
🍽️ **Калории:** {avg_calories:.0f} / {user_goals['calories']} ккал ({avg_calories_percent:.1f}%)
{avg_calories_bar}

🥩 **Белки:** {avg_protein:.1f} / {user_goals['protein']}г ({avg_protein_percent:.1f}%)
{avg_protein_bar}

🧈 **Жиры:** {avg_fats:.1f} / {user_goals['fats']}г ({avg_fats_percent:.1f}%)
{avg_fats_bar}

🍞 **Углеводы:** {avg_carbs:.1f} / {user_goals['carbs']}г ({avg_carbs_percent:.1f}%)
{avg_carbs_bar}

📅 Период: {date.today().strftime('%d.%m.%Y')}
"""
            return report.strip()
            
        except Exception as e:
            logger.error(f"Ошибка форматирования недельного отчета: {e}")
            return "❌ Ошибка генерации отчета"
    
    @staticmethod
    def format_nutrition_result(nutrition_data: Dict[str, Any]) -> str:
        """Форматировать результат анализа одного изображения"""
        try:
            food_name = nutrition_data.get('food_name', 'неизвестно')
            calories = nutrition_data.get('calories', 0)
            protein = nutrition_data.get('protein', 0)
            fats = nutrition_data.get('fats', 0)
            carbs = nutrition_data.get('carbs', 0)
            confidence = nutrition_data.get('confidence', 0)
            
            confidence_emoji = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
            
            result = f"""
🍽️ *Анализ завершен!*

📝 **Блюдо:** {food_name}
{confidence_emoji} **Уверенность:** {confidence:.1%}

📊 **Питательная ценность:**
🍽️ Калории: {calories:.0f} ккал
🥩 Белки: {protein:.1f}г
🧈 Жиры: {fats:.1f}г
🍞 Углеводы: {carbs:.1f}г

✅ Данные сохранены в ваш дневник!
"""
            return result.strip()
            
        except Exception as e:
            logger.error(f"Ошибка форматирования результата анализа: {e}")
            return "❌ Ошибка форматирования результата"

    @staticmethod
    def format_water_status(today_ml: int, goal_ml: int) -> str:
        try:
            percent = min((today_ml / goal_ml) * 100, 100) if goal_ml else 0
            bar = ReportGenerator._create_progress_bar(percent)
            return (
                f"💧 Вода за сегодня: {today_ml} / {goal_ml} мл ({percent:.0f}%)\n{bar}"
            )
        except Exception:
            return "💧 Вода: ошибка расчета"

    @staticmethod
    def format_weekly_water(bars: Dict[str, int]) -> str:
        """Простой график воды по дням недели: { 'Пн': 1500, ... }"""
        try:
            lines = ["📈 Вода за неделю:"]
            max_ml = max(bars.values()) if bars else 0
            scale = max(1, max_ml // 10) if max_ml else 1
            for day, ml in bars.items():
                blocks = ml // scale if scale else 0
                lines.append(f"{day}: " + ("█" * int(blocks)))
            return "\n".join(lines)
        except Exception:
            return "📈 Вода за неделю: ошибка отображения"
    
    @staticmethod
    def _create_progress_bar(percentage: float, length: int = 10) -> str:
        """Создать текстовый прогресс-бар"""
        try:
            filled_length = int((percentage / 100) * length)
            bar = "█" * filled_length + "░" * (length - filled_length)
            return bar
        except Exception:
            return "░" * length
    
    @staticmethod
    def get_welcome_message() -> str:
        """Получить приветственное сообщение"""
        return """
🤖 *Добро пожаловать в КБЖУ Анализатор!*

Я помогу вам отслеживать ваше питание. Просто отправьте мне фотографию еды, и я проанализирую её калорийность и состав.

📋 **Доступные команды:**
/start - Начать работу
/stats - Статистика за сегодня
/week - Статистика за неделю
/help - Справка

📸 **Как использовать:**
1. Сфотографируйте вашу еду
2. Отправьте фото мне
3. Получите анализ КБЖУ
4. Просматривайте статистику

Начните прямо сейчас - отправьте фото еды! 🍽️
"""
    
    @staticmethod
    def get_help_message() -> str:
        """Получить сообщение справки"""
        return """
📖 *Справка по использованию*

🤖 **Основные функции:**
• Анализ КБЖУ по фотографиям еды
• Отслеживание дневного потребления
• Недельная статистика
• Персональные цели питания

📸 **Отправка фотографий:**
• Поддерживаемые форматы: JPG, PNG, WEBP
• Максимальный размер: 20MB
• Фотографируйте еду в хорошем освещении

📊 **Команды:**
/stats - Показать статистику за сегодня
/week - Показать статистику за неделю
/help - Показать эту справку

💡 **Советы для лучшего анализа:**
• Фотографируйте еду сверху
• Убедитесь в хорошем освещении
• Покажите всю порцию целиком
• Избегайте размытых снимков

❓ **Есть вопросы?** Обратитесь к разработчику.
"""
