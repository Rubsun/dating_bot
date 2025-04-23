import httpx
from aiogram import Router, F
from aiogram import types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from components.api_gateway.controllers.bot.keyboards import gender_kb, remove_kb, skip_kb
from components.api_gateway.controllers.bot.states import ProfileCreationStates

router = Router()


@router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    async with httpx.Client() as client:
        response = await client.get(f"http://localhost:8001/api/v1/profiles/telegram/{user_id}")  # TODO Получение профиля юзера

        if response.status_code == 404:
            await state.update_data(
                user_id=user_id,
            )

            await state.set_state(ProfileCreationStates.waiting_for_first_name)

            await message.answer(
                f"Привет, {first_name}! 👋 Добро пожаловать в Дэйтинг Бот!\n"
                "Чтобы другие могли тебя найти, давай создадим твою анкету.\n\n"
                "📝 <b>Как тебя зовут</b> (Это имя будут видеть другие пользователи)",
                parse_mode="HTML",
            )


        elif response.status_code == 200:
            await message.answer("Ваша анкета активна. Зайдите в веб приложение")  # TODO отправить ссылку с апкой


@router.message(ProfileCreationStates.waiting_for_first_name)
async def waiting_for_first_name(message: types.Message, state: FSMContext):
    first_name = message.text

    await state.update_data(first_name=first_name)
    await state.set_state(ProfileCreationStates.waiting_for_last_name)
    await message.answer(f"Теперь введи свою фамилию")


@router.message(ProfileCreationStates.waiting_for_last_name)
async def waiting_for_last_name(message: types.Message, state: FSMContext):
    last_name = message.text
    await state.update_data(last_name=last_name)
    await state.set_state(ProfileCreationStates.waiting_for_bio)
    await message.answer("Введите описание для профиля одним сообщением\n\nИли нажмите 'Пропустить'",
                         reply_markup=skip_kb)


@router.message(ProfileCreationStates.waiting_for_bio)
async def waiting_for_bio(message: types.Message, state: FSMContext):
    bio = message.text.strip()

    if bio.lower() == "пропустить":
        bio = ""

    await state.update_data(bio=bio)
    await state.set_state(ProfileCreationStates.waiting_for_age)
    await message.answer("Введите свой возраст", reply_markup=remove_kb)


@router.message(ProfileCreationStates.waiting_for_age)
async def waiting_for_age(message: types.Message, state: FSMContext):
    age_text = message.text
    if not age_text.isdigit():
        await message.answer("Пожалуйста, введите возраст числом.")
        return

    age = int(age_text)
    if age <= 16:
        await message.answer("Регистрация доступна только пользователям старше 16 лет.")
        return

    await state.update_data(age=age)
    await state.set_state(ProfileCreationStates.waiting_for_gender)
    await message.answer(text="Кто вы", reply_markup=gender_kb)



@router.callback_query(F.data.startswith("select_gender_"),
                       StateFilter(ProfileCreationStates.waiting_for_gender))
async def select_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await state.set_state(ProfileCreationStates.waiting_for_city)
    await callback.message.edit_text("Введите ваш город")


@router.message(ProfileCreationStates.waiting_for_city)
async def waiting_for_city(message: types.Message, state: FSMContext):
    city = message.text.strip()
    if not (city.istitle() and city.isalpha()):
        await message.answer("Название города должно начинаться с заглавной буквы и содержать только буквы.")
        return

    await state.update_data(city=city)
    await state.set_state(ProfileCreationStates.waiting_for_photo)
    await message.answer("Пришлите фото для вашего профиля")


@router.message(ProfileCreationStates.waiting_for_photo)
async def waiting_for_photo(message: types.Message, state: FSMContext):
    profile_data = await state.get_data()
    photo_bytes = None

    # Пользователь отправил фото
    if message.photo:
        photo = message.photo[-1]
        file_info = await message.bot.get_file(photo.file_id)
        file = await message.bot.download_file(file_info.file_path)
        photo_bytes = file.read()

    # Пользователь написал "Пропустить"
    elif message.text and message.text.strip().lower() == "пропустить":
        photo_bytes = b""

    else:
        await message.answer("Пожалуйста, отправьте фотографию или нажмите 'Пропустить'")
        return

    await message.answer("Вы успешно создали свою анкету!", reply_markup=remove_kb)

    form_data = {
        "user_id": str(profile_data["user_id"]),
        "first_name": profile_data["first_name"],
        "last_name": profile_data["last_name"],
        "bio": profile_data.get("bio", ""),
        "age": profile_data["age"],
        "gender": profile_data["gender"],
        "city": profile_data["city"],
    }

    files = {"photo": photo_bytes} if photo_bytes else {}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/v1/profiles/",
            data=form_data,
            files=files
        )
        if response.status_code == 201:
            await message.answer("✅ Ваша анкета успешно создана!")
        else:
            await message.answer("❌ Произошла ошибка при создании анкеты.")

    await state.clear()
