from datetime import datetime, date
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    @staticmethod
    def format_daily_report(nutrition_data: Dict[str, float], user_goals: Dict[str, int] = None, user_stats: Dict[str, int] = None) -> str:
        """Format daily nutrition report"""
        try:
            calories = nutrition_data.get('calories', 0)
            protein = nutrition_data.get('protein', 0)
            fats = nutrition_data.get('fats', 0)
            carbs = nutrition_data.get('carbs', 0)
            
            # Получаем статистику пользователя
            total_photos_sent = user_stats.get('total_photos_sent', 0) if user_stats else 0
            
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
📊 *Daily Nutrition Report*

🍽️ **Calories:** {calories:.0f} / {user_goals['calories']} kcal ({calories_percent:.1f}%)
{calories_bar}

🥩 **Protein:** {protein:.1f} / {user_goals['protein']} g ({protein_percent:.1f}%)
{protein_bar}

🧈 **Fats:** {fats:.1f} / {user_goals['fats']} g ({fats_percent:.1f}%)
{fats_bar}

🍞 **Carbs:** {carbs:.1f} / {user_goals['carbs']} g ({carbs_percent:.1f}%)
{carbs_bar}

📸 **Photos sent:** {total_photos_sent} total
📅 Date: {date.today().strftime('%Y-%m-%d')}
"""
            return report.strip()
            
        except Exception as e:
            logger.error(f"Daily report formatting error: {e}")
            return "❌ Report generation error"
    
    @staticmethod
    def format_weekly_report(week_data: Dict[str, float], user_goals: Dict[str, int] = None) -> str:
        """Format weekly nutrition report"""
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
📈 *Weekly Nutrition Report*

📊 **Totals for the week:**
🍽️ Calories: {total_calories:.0f} kcal
🥩 Protein: {total_protein:.1f} g
🧈 Fats: {total_fats:.1f} g
🍞 Carbs: {total_carbs:.1f} g

📅 **Daily averages:**
🍽️ **Calories:** {avg_calories:.0f} / {user_goals['calories']} kcal ({avg_calories_percent:.1f}%)
{avg_calories_bar}

🥩 **Protein:** {avg_protein:.1f} / {user_goals['protein']} g ({avg_protein_percent:.1f}%)
{avg_protein_bar}

🧈 **Fats:** {avg_fats:.1f} / {user_goals['fats']} g ({avg_fats_percent:.1f}%)
{avg_fats_bar}

🍞 **Carbs:** {avg_carbs:.1f} / {user_goals['carbs']} g ({avg_carbs_percent:.1f}%)
{avg_carbs_bar}

📅 Period end: {date.today().strftime('%Y-%m-%d')}
"""
            return report.strip()
            
        except Exception as e:
            logger.error(f"Weekly report formatting error: {e}")
            return "❌ Report generation error"
    
    @staticmethod
    def format_nutrition_result(nutrition_data: Dict[str, Any]) -> str:
        """Format single image analysis result"""
        try:
            food_name = nutrition_data.get('food_name', 'unknown')
            calories = nutrition_data.get('calories', 0)
            protein = nutrition_data.get('protein', 0)
            fats = nutrition_data.get('fats', 0)
            carbs = nutrition_data.get('carbs', 0)
            weight_grams = nutrition_data.get('weight_grams')
            
            confidence_emoji = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
            
            weight_line = f"⚖️ Weight: {weight_grams:.0f} g\n" if weight_grams else ""
            result = f"""
🍽️ *Analysis complete!*

📝 **Dish:** {food_name}

📊 **Nutrition (estimated):**
🍽️ Calories: {calories:.0f} kcal
🥩 Protein: {protein:.1f} g
🧈 Fats: {fats:.1f} g
🍞 Carbs: {carbs:.1f} g

{weight_line}

✅ Saved to your diary!
"""
            return result.strip()
            
        except Exception as e:
            logger.error(f"Analysis result formatting error: {e}")
            return "❌ Formatting error"

    @staticmethod
    def format_water_status(today_ml: int, goal_ml: int) -> str:
        try:
            percent = min((today_ml / goal_ml) * 100, 100) if goal_ml else 0
            bar = ReportGenerator._create_progress_bar(percent)
            return (
                f"💧 Water today: {today_ml} / {goal_ml} ml ({percent:.0f}%)\n{bar}"
            )
        except Exception:
            return "💧 Вода: ошибка расчета"

    @staticmethod
    def format_weekly_water(bars: Dict[str, int]) -> str:
        """Simple weekly water chart: { 'Mon': 1500, ... }"""
        try:
            lines = ["📈 Weekly water:"]
            max_ml = max(bars.values()) if bars else 0
            scale = max(1, max_ml // 10) if max_ml else 1
            for day, ml in bars.items():
                blocks = ml // scale if scale else 0
                lines.append(f"{day}: " + ("█" * int(blocks)))
            return "\n".join(lines)
        except Exception:
            return "📈 Weekly water: display error"
    
    @staticmethod
    def _create_progress_bar(percentage: float, length: int = 10) -> str:
        """Create a text progress bar"""
        try:
            filled_length = int((percentage / 100) * length)
            bar = "█" * filled_length + "░" * (length - filled_length)
            return bar
        except Exception:
            return "░" * length
    
    @staticmethod
    def get_welcome_message() -> str:
        """Get welcome message (English)"""
        return """
🤖 *Welcome to the Nutrition Analyzer!*

Send a photo of your meal and I will estimate calories, protein, fats and carbs.

📋 **Commands:**
/start - Start
/stats - Today stats
/week - Weekly stats
/help - Help

📸 **How to use:**
1. Take a photo of your meal
2. Send it here
3. Get the nutrition analysis
4. Track your progress

Send your first photo now! 🍽️
"""
    
    @staticmethod
    def get_help_message() -> str:
        """Get help message (English)"""
        return """
📖 *Help*

🤖 **Features:**
• Vision-based nutrition analysis
• Daily and weekly stats
• Personal goals

📸 **Images:**
• Formats: JPG, PNG, WEBP
• Max size: 20MB
• Good lighting recommended

📊 **Commands:**
/stats - Today stats
/week - Weekly stats
/help - This help

💡 **Tips:**
• Shoot from top
• Ensure good lighting
• Include the whole portion

❓ Questions? Contact support.
"""
