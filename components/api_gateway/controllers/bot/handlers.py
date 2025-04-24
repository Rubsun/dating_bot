import logging

import httpx
from aiogram import Router, F, Bot
from aiogram import types
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from components.api_gateway.controllers.bot.keyboards import gender_kb, remove_kb, skip_kb
from components.api_gateway.controllers.bot.states import ProfileCreationStates

router = Router()

DEFAULT_PROFILE_PHOTO_ID = "AgACAgIAAxkBAAInBWgKBbyXVV1FRr3Ox4s7AuynlXQVAAKO9DEbRd1RSCfD3X6lDdSLAQADAgADbQADNgQ"


@router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    async with httpx.AsyncClient() as client:
        profile_service_url = "http://localhost:8000/api/v1/profiles"
        response = await client.get(f"{profile_service_url}/{user_id}")

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
            await message.answer("Ваша анкета активна. Можете посмотреть свою анкету командой /profile или начать просмотр других анкет командой /view")
        else:
            await message.answer(f"Произошла ошибка при проверке профиля: {response.status_code}")


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


@router.callback_query(F.data.startswith("gender_"),
                       StateFilter(ProfileCreationStates.waiting_for_gender))
async def select_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await state.set_state(ProfileCreationStates.waiting_for_city)
    await callback.message.edit_text("Введите ваш город")
    await callback.answer()


@router.message(ProfileCreationStates.waiting_for_city)
async def waiting_for_city(message: types.Message, state: FSMContext):
    city = message.text.strip()
    if not (city.istitle() and city.isalpha()):
        await message.answer("Название города должно начинаться с заглавной буквы и содержать только буквы.")
        return
    await state.update_data(city=city)
    await state.set_state(ProfileCreationStates.waiting_for_photo)
    await message.answer("Пришлите фото для вашего профиля (или нажмите 'Пропустить')", reply_markup=skip_kb)

@router.message(ProfileCreationStates.waiting_for_photo, F.photo | (F.text.lower() == "пропустить"))
async def waiting_for_photo(message: types.Message, state: FSMContext):
    profile_data = await state.get_data()
    photo_bytes = None
    photo_file_id = None

    if message.photo is not None and (message.photo[-1] is not None):
        logging.info("Fimoz: %s, %s", message.photo, message.photo[-1])
        logging.info('if message.photo')
        photo = message.photo[-1]
        photo_file_id = photo.file_id
        file_info = await message.bot.get_file(photo.file_id)
        file = await message.bot.download_file(file_info.file_path)
        photo_bytes = file.read()
    elif message.text and message.text.strip().lower() == "пропустить":
        logging.info('if message.text')
        photo_bytes = None
    else:
        await message.answer("Пожалуйста, отправьте фотографию или нажмите 'Пропустить'")
        return

    if photo_file_id:
        logging.info(f"file id: {photo_file_id}")
        await state.update_data(photo_file_id=photo_file_id)

    await message.answer("Сохраняем вашу анкету...", reply_markup=remove_kb)

    refill = profile_data.get("refill")
    if refill:
        logging.info("refill: %s. Deleting profile..", refill)

        profile_service_url = "http://localhost:8000/api/v1/profiles"
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{profile_service_url}/{profile_data['user_id']}")
            logging.info("Deletion status: %d; data: %s", response.status_code, response.json())

        await state.update_data(
            refill=None,
        )


    payload_data = {
        "telegram_id": profile_data["user_id"],
        "first_name": profile_data["first_name"],
        "last_name": profile_data["last_name"],
        "bio": profile_data.get("bio", ""),
        "age": profile_data["age"],
        "gender": profile_data["gender"],
        "city": profile_data["city"],
        "photo_file_id": photo_file_id
    }

    profile_service_url = "http://localhost:8000/api/v1/profiles"

    print('Trying to create profile...')
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = None
            form_data_str = {k: str(v) for k, v in payload_data.items()}

            files = {}
            if photo_bytes:
                files["photo"] = ("profile_photo.jpg", photo_bytes, "image/jpeg")

            response = await client.post(
                profile_service_url,
                data=form_data_str,
                files=files
            )
            print('Create profile resp:', response.json())
            print('Payload:', form_data_str)

            if response.status_code in (200, 201):
                rating_service_url = "http://localhost:8001/api/v1/ratings"
                try:
                    async with httpx.AsyncClient() as rating_client:
                        rating_response = await rating_client.post(
                            rating_service_url,
                            json=payload_data
                        )
                        if rating_response.status_code not in (200, 201):
                            logging.warning(
                                f"Не удалось создать рейтинг: {rating_response.status_code} {rating_response.text}")
                except Exception as e:
                    logging.error(f"Ошибка при создании рейтинга: {e}")

                await message.answer(
                    "✅ Ваша анкета успешно создана! Можете начать просмотр других анкет командой /view")
                await state.clear()
            elif response.status_code == 422:
                await message.answer(f"❌ Ошибка валидации данных при создании анкеты: {response.text}")
            elif response.status_code == 400:
                await message.answer(f"❌ Ошибка в данных при создании анкеты: {response.text}")
            else:
                await message.answer(f"❌ Произошла ошибка при создании анкеты: {response.status_code} {response.text}")

    except httpx.RequestError as e:
        await message.answer(f"❌ Ошибка сети при создании анкеты: {e}")
    except Exception as e:
        await message.answer(f"❌ Непредвиденная ошибка при создании анкеты: {e}")
        await state.clear()



class ViewingStates(StatesGroup):
    viewing = State()


def get_rating_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="👍 Лайк", callback_data="rate:like"),
            InlineKeyboardButton(text="👎 Дизлайк", callback_data="rate:dislike"),
        ],
        [
            InlineKeyboardButton(text="❌ Закончить просмотр", callback_data="rate:stop"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)



async def show_next_profile(message: types.Message, state: FSMContext):
    current_user_id = message.chat.id
    data = await state.get_data()

    profile_service_url = "http://localhost:8000/api/v1/profiles"
    next_profile_url = f"{profile_service_url}/next/{current_user_id}?offset={data.get('view_offset', 0)}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(next_profile_url)

            if response.status_code == 200:
                profile_data = response.json()
                await state.update_data(
                    viewing_profile_id=profile_data['user_id'],
                    view_offset=data.get('view_offset', 0) + 1
                )
                await state.set_state(ViewingStates.viewing)

                caption = (
                    f"<b>{profile_data['first_name']} {profile_data.get('last_name', '')}, {profile_data['age']}</b>, {profile_data['city']}\n"
                    f"Пол: {'М' if profile_data['gender'] == 'male' else 'Ж'}\n\n"
                    f"{'О себе: ' + profile_data.get('bio') if profile_data.get('bio') != '' else 'Нет описания'}"
                )

                keyboard = get_rating_keyboard()

                if profile_data.get('photo_file_id') and profile_data.get('photo_file_id') != "None":
                    logging.info(profile_data['photo_file_id'])
                    await message.answer_photo(
                        photo=profile_data['photo_file_id'],
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await message.answer_photo(
                        photo=DEFAULT_PROFILE_PHOTO_ID,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )

            elif response.status_code == 404:
                await message.answer("🤷‍♀️ Анкеты для просмотра закончились. Попробуйте позже.", reply_markup=remove_kb)
                await state.clear()
            else:
                await message.answer(f"😕 Не удалось загрузить анкету. Ошибка: {response.status_code}",
                                     reply_markup=remove_kb)
                await state.clear()

    except httpx.RequestError as e:
        await message.answer(f"❌ Ошибка сети при загрузке анкеты: {e}", reply_markup=remove_kb)
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Непредвиденная ошибка при загрузке анкеты: {e}", reply_markup=remove_kb)
        await state.clear()


@router.message(Command("view"), StateFilter(None))
async def view_profiles_command(message: types.Message, state: FSMContext):
    async with httpx.AsyncClient() as client:
        profile_service_url = "http://localhost:8000/api/v1/profiles"
        response = await client.get(f"{profile_service_url}/{message.from_user.id}")
        if response.status_code == 200:
            await message.answer("Начинаем просмотр анкет...")
            await show_next_profile(message, state)
        elif response.status_code == 404:
            await message.answer("Сначала вам нужно создать свою анкету. Введите /start")
        else:
            await message.answer(f"Не удалось проверить вашу анкету. Ошибка: {response.status_code}")



@router.callback_query(StateFilter(ViewingStates.viewing), F.data.startswith("rate:"))
async def process_rating_callback(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    current_user_id = callback.from_user.id
    state_data = await state.get_data()
    viewing_profile_id = state_data.get('viewing_profile_id')

    if not viewing_profile_id:
        await callback.answer("Ошибка: не найдена анкета для оценки.", show_alert=True)
        await state.clear()
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    await callback.message.edit_reply_markup(reply_markup=None)

    if action == "stop":
        await callback.message.answer("Просмотр анкет завершен.", reply_markup=remove_kb)
        await state.clear()
        await callback.answer()
        return

    rating_service_url = "http://localhost:8001/api/v1/ratings"
    endpoint = f"{rating_service_url}/{action}"

    payload = {
        "rater_user_id": current_user_id,
        "rated_user_id": viewing_profile_id
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=payload)

        if response.status_code == 200:
            await callback.answer(f"Вы поставили {('лайк' if action == 'like' else 'дизлайк')}!")
            # Показать следующую анкету
            await show_next_profile(callback.message, state)
        else:
            await callback.answer(f"Ошибка при отправке оценки: {response.status_code}", show_alert=True)
            await callback.message.answer("Не удалось обработать ваш голос. Попробуйте позже.")
            await state.clear()

    except httpx.RequestError as e:
        await callback.answer(f"Ошибка сети: {e}", show_alert=True)
        await callback.message.answer("Ошибка сети. Попробуйте позже.")
        await state.clear()
    except Exception as e:
        await callback.answer(f"Непредвидённая ошибка: {e}", show_alert=True)
        await callback.message.answer("Что-то пошло не так.")
        await state.clear()


@router.message(Command("profile"), StateFilter(None))
async def get_my_profile(message: types.Message, state: FSMContext):
    async with httpx.AsyncClient() as client:
        profile_service_url = "http://localhost:8000/api/v1/profiles"
        response = await client.get(f"{profile_service_url}/{message.from_user.id}")

        if response.status_code == 200:
            profile_data = response.json()
            caption = (
                f"<b>{profile_data['first_name']} {profile_data.get('last_name', '')}, {profile_data['age']}</b>, {profile_data['city']}\n"
                f"Пол: {'М' if profile_data['gender'] == 'male' else 'Ж'}\n\n"
                f"{'О себе: ' + profile_data.get('bio') if profile_data.get('bio') != '' else 'Нет описания'}"
            )
            keyboard = get_my_profile_keyboard()

            if profile_data.get('photo_file_id') and profile_data.get('photo_file_id') != "None":
                await message.answer_photo(
                    photo=profile_data['photo_file_id'],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                await message.answer_photo(
                    photo=DEFAULT_PROFILE_PHOTO_ID,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
        elif response.status_code == 404:
            await message.answer("Сначала вам нужно создать свою анкету. Введите /start")
        else:
            await message.answer(f"Не удалось проверить вашу анкету. Ошибка: {response.status_code}")


@router.callback_query(F.data == 'my_profile-reset')
async def fill_profile_again(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(
        user_id=callback.from_user.id,
        refill=True,
    )
    await state.set_state(ProfileCreationStates.waiting_for_first_name)
    await callback.message.answer(
        "📝 <b>Как тебя зовут</b> (Это имя будут видеть другие пользователи)",
        parse_mode="HTML",
    )

@router.message(F.content_type == 'photo')
async def get_photo(message: types.Message, state: FSMContext):
    print(message.photo[-1].file_id)


def get_my_profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Заполнить заново', callback_data='my_profile-reset')]
        ]
    )
