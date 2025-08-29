import openai
import base64
import json
import logging
from PIL import Image
import io
from config.settings import settings
from models.data_models import NutritionAnalysis


class OpenAIQuotaError(Exception):
    """Исключение исчерпания квоты OpenAI (HTTP 429 insufficient_quota)"""
    pass

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if getattr(settings, "OPENAI_ORG_ID", None):
            client_kwargs["organization"] = settings.OPENAI_ORG_ID
        self.client = openai.OpenAI(**client_kwargs)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.MAX_TOKENS
    
    def _compress_image(self, image_bytes: bytes, max_size: int = 1024) -> bytes:
        """Сжать изображение до указанного размера"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Конвертируем в RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Изменяем размер, сохраняя пропорции
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Сохраняем в байты
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Ошибка сжатия изображения: {e}")
            return image_bytes
    
    def _encode_image(self, image_bytes: bytes) -> str:
        """Кодировать изображение в base64"""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def _create_prompt(self) -> str:
        """Создать промпт для анализа изображения"""
        return """
        Проанализируй это изображение еды и определи примерные значения КБЖУ (калории, белки, жиры, углеводы).
        
        Верни ответ ТОЛЬКО в формате JSON без дополнительного текста:
        {
            "calories": число (калории),
            "protein": число (белки в граммах),
            "fats": число (жиры в граммах),
            "carbs": число (углеводы в граммах),
            "food_name": "название блюда или продукта",
            "confidence": число от 0 до 1 (уверенность в анализе)
        }
        
        Если на изображении нет еды или ты не можешь определить, что это, верни:
        {
            "calories": 0,
            "protein": 0,
            "fats": 0,
            "carbs": 0,
            "food_name": "неизвестно",
            "confidence": 0
        }
        
        Оценивай порцию реалистично. Если видишь готовое блюдо, оценивай его как целую порцию.
        """
    
    def analyze_food_image(self, image_bytes: bytes) -> NutritionAnalysis:
        """Анализировать изображение еды через OpenAI Vision API"""
        try:
            # Сжимаем изображение
            compressed_image = self._compress_image(image_bytes)
            
            # Кодируем в base64
            base64_image = self._encode_image(compressed_image)
            
            # Создаем промпт
            prompt = self._create_prompt()
            
            # Отправляем запрос к OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens
            )
            
            # Парсим ответ
            content = response.choices[0].message.content.strip()
            
            # Извлекаем JSON из ответа
            try:
                # Ищем JSON в ответе
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    nutrition_data = json.loads(json_str)
                else:
                    raise ValueError("JSON не найден в ответе")
                
                # Валидируем данные
                nutrition_analysis = NutritionAnalysis(
                    calories=float(nutrition_data.get('calories', 0)),
                    protein=float(nutrition_data.get('protein', 0)),
                    fats=float(nutrition_data.get('fats', 0)),
                    carbs=float(nutrition_data.get('carbs', 0)),
                    food_name=str(nutrition_data.get('food_name', 'неизвестно')),
                    confidence=float(nutrition_data.get('confidence', 0))
                )
                
                logger.info(f"Успешный анализ изображения: {nutrition_analysis.food_name}")
                return nutrition_analysis
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"Ошибка парсинга JSON ответа: {e}")
                logger.error(f"Полученный ответ: {content}")
                # Сигнализируем об ошибке наверх, чтобы обработчик сообщений не сохранял пустые данные
                raise
                
        except Exception as e:
            err_text = str(e)
            # Отдельно обрабатываем исчерпание квоты
            if "insufficient_quota" in err_text or "429" in err_text:
                logger.error("OpenAI: исчерпана квота/получен 429. Останавливаю анализ.")
                raise OpenAIQuotaError(err_text)
            logger.error(f"Ошибка анализа изображения через OpenAI: {e}")
            # Пробрасываем дальше, чтобы внешний код корректно обработал и не сохранял данные
            raise
