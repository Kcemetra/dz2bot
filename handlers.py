from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import ProfileStates, FoodStates
from database import update_user, get_user, log_water, log_calories, log_workout_db
from api import get_temperature, analyze_food_hybrid
from graphics import generate_progress_chart

router = Router()

# инлайн клавиатура
gender_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]],
    resize_keyboard=True, one_time_keyboard=True
)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Привет! Я трекер воды и калорий.\nНастрой профиль командой /set_profile")


# настройка профиля

@router.message(Command("set_profile"))
async def set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(ProfileStates.weight)

@router.message(ProfileStates.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(ProfileStates.height)


@router.message(ProfileStates.height)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=float(message.text))
    await message.reply("Введите ваш возраст:")
    await state.set_state(ProfileStates.age)


@router.message(ProfileStates.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await message.reply("Укажите ваш пол:", reply_markup=gender_kb)
    await state.set_state(ProfileStates.gender)


@router.message(ProfileStates.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(ProfileStates.activity)


@router.message(ProfileStates.activity)
async def process_activity(message: Message, state: FSMContext):
    await state.update_data(activity=int(message.text))
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(ProfileStates.city)

# рассчитываем воду с учетом погоды, рассчитываем калории, сохраняем в БД
@router.message(ProfileStates.city)
async def process_city(message: Message, state: FSMContext):
    data = await state.get_data()
    city = message.text
    weight = data['weight']
    activity = data['activity']

    temp = await get_temperature(city)
    water_goal = weight * 30 + (activity // 30) * 500
    if temp > 25:
        water_goal += 500
    if data['gender'] == "Мужской":
        bmr = 10 * weight + 6.25 * data['height'] - 5 * data['age'] + 5
    else:
        bmr = 10 * weight + 6.25 * data['height'] - 5 * data['age'] - 161
    calorie_goal = bmr + (activity * 5)

    await update_user(
        message.from_user.id,
        weight=weight, height=data['height'], age=data['age'],
        gender=data['gender'], activity=activity, city=city,
        water_goal=water_goal, calorie_goal=calorie_goal,
        logged_water=0, logged_calories=0, burned_calories=0
    )

    await message.reply(f"Профиль настроен!\nВаша норма воды: {water_goal} мл\nВаша норма калорий: {calorie_goal} ккал")
    await state.clear()


# логирование воды
@router.message(Command("log_water"))
async def log_w(message: Message):
    try:
        amount = float(message.text.split()[1])
        await log_water(message.from_user.id, amount)
        user = await get_user(message.from_user.id)
        left = max(0, user['water_goal'] - user['logged_water'])
        await message.reply(f"Записано {amount} мл. Осталось выпить {left} мл.")
    except:
        await message.reply("Используйте формат: /log_water <количество_в_мл>")


# логирование, обработка еды

@router.message(Command("log_food"))
async def cmd_log_food(message: Message, state: FSMContext):
    await message.reply(
        "🍔 Опишите, что вы съели (например: '200г творога и банан')\n"
        "📸 Или просто пришлите фотографию вашей еды! (можно прислать и фото и текст)"
    )
    await state.set_state(FoodStates.waiting_for_food)


@router.message(FoodStates.waiting_for_food, F.content_type.in_({'text', 'photo'}))
async def process_food(message: Message, state: FSMContext, bot: Bot):
    processing_msg = await message.reply("⏳ анализируем вашу еду...")

    image_bytes = None
    text_desc = message.caption if message.photo else message.text

    if message.photo:
        photo_file = await bot.get_file(message.photo[-1].file_id)
        photo_bytes_io = await bot.download_file(photo_file.file_path)
        image_bytes = photo_bytes_io.read()

    food_info = await analyze_food_hybrid(text=text_desc, image_bytes=image_bytes)

    if not food_info or food_info['calories'] == 0:
        await processing_msg.edit_text("❌ не удалось распознать еду. Попробуйте описать подробнее.")
        await state.clear()
        return

    cal = round(food_info['calories'], 1)
    source = food_info['source']

    await log_calories(message.from_user.id, cal)

    await processing_msg.edit_text(
        f"✅ Еда распознана!\n"
        f"🍽 Продукт: {food_info['name']}\n"
        f"🔥 Калорийность: {cal} ккал\n"
        f"🤖 Анализ выполнен через: {source}"
    )
    await state.clear()


# логирование тренировок
@router.message(Command("log_workout"))
async def log_wo(message: Message):
    try:
        args = message.text.split()
        workout_type = args[1]
        minutes = int(args[2])

        burned = minutes * 10
        extra_water = (minutes // 30) * 200

        await log_workout_db(message.from_user.id, burned, extra_water)
        await message.reply(
            f"🏃‍♂️ {workout_type} {minutes} мин — сожжено {burned} ккал.\n💧 Рекомендуем выпить еще {extra_water} мл воды.")
    except:
        await message.reply("Используйте: /log_workout <тип> <минуты>")

# проверка прогресса, с графиками и рекомендациями

@router.message(Command("check_progress"))
async def check_prog(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.reply("Сначала настройте профиль: /set_profile")
        return

    w_log, w_goal = user['logged_water'], user['water_goal']
    c_log, c_goal, c_burn = user['logged_calories'], user['calorie_goal'], user['burned_calories']

    text = (f"📊 Прогресс:\n"
            f"Вода: Выпито {w_log}/{w_goal} мл.\n"
            f"Калории: Потреблено {c_log}/{c_goal} ккал.\n"
            f"Сожжено: {c_burn} ккал.\n"
            f"Баланс калорий: {c_log - c_burn} ккал.")

    if c_goal - (c_log - c_burn) < 300:
        text += "\n⚠️ Внимание! Вы близки к норме калорий. Рекомендуем легкий ужин, например овощной салат с йогуртом."
    if w_log < w_goal / 2:
        text += "\n💧 Вы выпили меньше половины нормы воды. Не забудьте попить!"

    chart_buf = generate_progress_chart(w_log, w_goal, c_log, c_goal)
    photo = BufferedInputFile(chart_buf.read(), filename="progress.png")

    await message.answer_photo(photo=photo, caption=text)