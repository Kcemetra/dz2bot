import aiohttp
import json
import google.generativeai as genai
from config import WEATHER_API_KEY, GEMINI_API_KEY, NINJAS_API_KEY

# настройка gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# получаем температуру выбранного города
async def get_temperature(city: str) -> float:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data["main"]["temp"]
            return 20.0

# gemini анализирует еду пользователя и генерирует api запрос для calorieninjas
async def analyze_food_hybrid(text: str = None, image_bytes: bytes = None):
    try:
        # пишем промпт, добавляем к нему текст и фото, если оно будет. И отправляем
        prompt = """
        You are a nutrition expert. 
        Analyze the provided food description or image.
        Return ONLY a raw JSON format (without markdown backticks) with two keys:
        1. "ninja_query": Translate the food to an English CalorieNinjas query with approximate weights/quantities 
           (e.g., "150g cottage cheese and 1 banana"). 
        2. "gemini_calories": Your own estimation of total calories as an integer (in case the API fails).
        """

        contents = [prompt]
        if text:
            contents.append(f"User description: {text}")
        if image_bytes:
            contents.append({"mime_type": "image/jpeg", "data": image_bytes})

        response = model.generate_content(contents)

        # очищаем от маркдауна на всякий случай
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        gemini_data = json.loads(clean_json)

        ninja_query = gemini_data.get("ninja_query", "")
        fallback_calories = gemini_data.get("gemini_calories", 0)

        # отправляем api запрос, если с CalorieNinjas проблемы, гемини на подстраховке
        if ninja_query:
            api_url = 'https://api.calorieninjas.com/v1/nutrition?query=' + ninja_query
            headers = {'X-Api-Key': NINJAS_API_KEY}

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as ninja_response:
                    if ninja_response.status == 200:
                        ninja_data = await ninja_response.json()
                        total_calories = sum(item.get("calories", 0) for item in ninja_data.get("items", []))

                        if total_calories > 0:
                            return {"calories": total_calories, "source": "CalorieNinjas", "name": ninja_query}

        return {"calories": fallback_calories, "source": "Gemini AI", "name": text if text else "Распознано по фото"}

    except Exception as e:
        print(f"Ошибка анализа еды: {e}")
        return None