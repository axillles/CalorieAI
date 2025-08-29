import logging
import json
from typing import Optional

from models.data_models import NutritionAnalysis

logger = logging.getLogger(__name__)


class G4FService:
    """Простейший клиент g4f для тестового фолбэка.
    Внимание: g4f нестабилен, провайдеры меняются, качество ответов может отличаться.
    """

    def __init__(self):
        try:
            import g4f  # noqa: F401
            from g4f.client import Client  # type: ignore
            self._client = Client()
        except Exception as e:
            logger.error(f"G4F не инициализируется: {e}")
            self._client = None

    def _create_prompt(self) -> str:
        return (
            "Проанализируй это изображение еды по URL и верни только JSON со значениями КБЖУ: "
            '{"calories": number, "protein": number, "fats": number, "carbs": number, '
            '"food_name": string, "confidence": number}. '
            "Только JSON без пояснений. Если не распознано — верни нули и food_name=\"неизвестно\"."
        )

    def analyze_food_image_url(self, image_url: str, max_tokens: int = 500) -> Optional[NutritionAnalysis]:
        if not self._client:
            raise RuntimeError("G4F клиент не инициализирован")

        prompt = self._create_prompt()
        try:
            resp = self._client.chat.completions.create(
                model="gpt-4o-mini",  # g4f маппит имя на доступный провайдер, может игнорироваться
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ]}
                ],
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content.strip()

            # Попробуем извлечь JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx == -1 or end_idx <= 0:
                raise ValueError("JSON не найден в ответе g4f")

            json_str = content[start_idx:end_idx]
            data = json.loads(json_str)

            return NutritionAnalysis(
                calories=float(data.get('calories', 0)),
                protein=float(data.get('protein', 0)),
                fats=float(data.get('fats', 0)),
                carbs=float(data.get('carbs', 0)),
                food_name=str(data.get('food_name', 'неизвестно')),
                confidence=float(data.get('confidence', 0)),
            )

        except Exception as e:
            logger.error(f"Ошибка g4f анализа изображения: {e}")
            return None


