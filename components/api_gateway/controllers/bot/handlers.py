import logging
from datetime import datetime, timedelta

import httpx
from aiogram import Router, F, Bot
from aiogram import types
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dishka.integrations.aiogram import FromDishka

from components.api_gateway.config import Config
from components.api_gateway.utils import get_coordinates, get_city
from components.api_gateway.controllers.bot.keyboards import gender_kb, remove_kb, skip_kb, get_my_profile_keyboard, \
    gender_preferences_kb, get_rate_likers_keyboard, get_rating_keyboard
from components.api_gateway.controllers.bot.states import ProfileCreationStates, ViewingStates, ViewingLikerProfiles
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.deep_linking import decode_payload
from aiogram.utils.deep_linking import create_start_link



router = Router()

DEFAULT_PROFILE_PHOTO_ID = "AgACAgIAAxkBAAIvm2gPP8rF5_7hyL1m5ytSeCg5BStxAALO8jEbQ2OASPqQUbOZEJF7AQADAgADbQADNgQ"


@router.message(CommandStart(deep_link=True))
async def handler(message: types.Message, command: CommandObject, state: FSMContext, bot: Bot, cfg: FromDishka[Config]):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    await state.set_state(None)

    args = command.args
    inviter_id = decode_payload(args)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{cfg.profile_service_url}/profiles/{user_id}")

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
            ref_rating_response = await client.post(
                cfg.rating_service_url + f'/stats/ref/{inviter_id}'
            )
            if ref_rating_response.status_code != 200:
                logging.warning('Update rating when join by ref link: %s', ref_rating_response.json())

            await bot.send_message(
                inviter_id,
                text=f'Пользователь {message.from_user.username} присоединился по твоей реферальной ссылке. 📈Твой рейтинг повышен'
            )
        elif response.status_code == 200:
            await message.answer(
                "Ваша анкета активна. Можете посмотреть свою анкету командой /profile или начать просмотр других анкет командой /view")
        else:
            await message.answer(f"Произошла ошибка при проверке профиля: {response.status_code}")


@router.message(CommandStart(deep_link=False))
async def start_cmd(message: types.Message, state: FSMContext, cfg: FromDishka[Config]):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    await state.set_state(None)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{cfg.profile_service_url}/profiles/{user_id}")

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


@router.message(Command('referral'))
async def get_ref_link(message: types.Message, bot: Bot, cfg: FromDishka[Config]):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{cfg.profile_service_url}/profiles/{message.from_user.id}")
        if response.status_code == 200:
            link = await create_start_link(bot, str(message.from_user.id), encode=True)
            await message.answer(f"Ваша реферальная ссылка: {link}. Отправьте другу, чтобы повысить свой рейтинг :)")
        elif response.status_code == 404:
            await message.answer("Сначала вам нужно создать свою анкету. Введите /start")


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
async def select_gender(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await state.set_state(ProfileCreationStates.waiting_for_city)

    await callback.message.delete()
    await bot.send_message(callback.from_user.id, "Введите ваш город", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text='📍 Отправить геолокацию', request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    ))



@router.message(ProfileCreationStates.waiting_for_city, F.content_type == 'location')
async def handle_user_location(message: types.Message,  state: FSMContext, bot: Bot):
    lat = message.location.latitude
    lon = message.location.longitude

    city = get_city(latitude=lat, longitude=lon)
    await state.update_data(
        latitude=lat,
        longitude=lon,
        city=city,
    )

    temp_msg = await bot.send_message(message.from_user.id, "...", reply_markup=remove_kb)
    await temp_msg.delete()

    await state.set_state(ProfileCreationStates.waiting_for_gender_preference)
    await message.answer("Кого вы ищете?", reply_markup=gender_preferences_kb)


@router.message(ProfileCreationStates.waiting_for_city)
async def waiting_for_city(message: types.Message, state: FSMContext):
    city = message.text.strip()
    city_coords = get_coordinates(city)
    if city_coords is None:
        await message.answer("Такого города не существует. Введите город")
        return
    await state.update_data(
        latitude=city_coords[0],
        longitude=city_coords[1],
        city=city,
    )
    await state.set_state(ProfileCreationStates.waiting_for_gender_preference)
    await message.answer("Кого вы ищете?", reply_markup=gender_preferences_kb)


@router.callback_query(F.data.startswith("gender_pref"),
                       StateFilter(ProfileCreationStates.waiting_for_gender_preference))
async def waiting_for_gender_preference(callback: types.CallbackQuery, state: FSMContext):
    preferred_gender = callback.data.split(':')[1]
    await state.update_data(preferred_gender=preferred_gender)
    await state.set_state(ProfileCreationStates.waiting_for_age_preference)
    await callback.message.edit_text("Пришлите желаемый диапазон возраста в формате 'min_age-max_age (Пример: 18-35)'")


@router.message(F.text, StateFilter(ProfileCreationStates.waiting_for_age_preference))
async def waiting_for_age_preference(message: types.Message, state: FSMContext):
    try:
        min_age, max_age = message.text.split('-')
    except Exception as e:
        print(e)
        await message.answer('Плохой формат')
        return

    await state.update_data(
        preferred_min_age=min_age,
        preferred_max_age=max_age,
    )
    await state.set_state(ProfileCreationStates.waiting_for_photo)
    await message.answer("Пришлите фото для вашего профиля (или нажмите 'Пропустить')", reply_markup=skip_kb)



@router.message(ProfileCreationStates.waiting_for_photo, F.photo | F.media_group_id | (F.text.lower() == "пропустить"))
async def waiting_for_photo(message: types.Message, state: FSMContext, cfg: FromDishka[Config], media_group: list[types.PhotoSize] | None = None):
    profile_data = await state.get_data()
    print('cosn:', profile_data)

    photo_file_ids = []
    photo_file_bytes = []

    print(media_group)
    if media_group:
        logging.info('if media_group')
        for photo in media_group:
            photo_file_ids.append(photo.file_id)

            file_info = await message.bot.get_file(photo.file_id)
            file = await message.bot.download_file(file_info.file_path)
            photo_bytes = file.read()
            photo_file_bytes.append(photo_bytes)

    elif message.photo:
        logging.info("Fimoz: %s, %s", message.photo, message.photo[-1])
        logging.info('if message.photo')
        photo = message.photo[-1]
        photo_file_id = photo.file_id
        file_info = await message.bot.get_file(photo.file_id)
        file = await message.bot.download_file(file_info.file_path)
        photo_bytes = file.read()

        photo_file_ids.append(photo_file_id)
        photo_file_bytes.append(photo_bytes)

    elif message.text and message.text.strip().lower() == "пропустить":
        logging.info('if message.text')
    else:
        await message.answer("Пожалуйста, отправьте фотографию/и или нажмите 'Пропустить'")
        return

    if len(photo_file_ids) > 0:
        logging.info(f"file ids: {photo_file_ids}")
        await state.update_data(photo_file_ids=photo_file_ids)

    await message.answer("Сохраняем вашу анкету...", reply_markup=remove_kb)

    new_profile_data = {
        "telegram_id": profile_data["user_id"],
        "first_name": profile_data["first_name"],
        "last_name": profile_data["last_name"],
        "tg_username": message.from_user.username,
        "bio": profile_data.get("bio", ""),
        "age": profile_data["age"],
        "gender": profile_data["gender"],
        "city": profile_data['city'],
        "photo_file_ids": photo_file_ids
    }

    new_preferences_data = {
        "user_id": profile_data['user_id'],
        "age": profile_data['age'],
        "gender": profile_data['gender'],
        "latitude": profile_data["latitude"],
        "longitude": profile_data["longitude"],
        "preferred_gender": profile_data["preferred_gender"],
        "preferred_min_age": profile_data["preferred_min_age"],
        "preferred_max_age": profile_data["preferred_max_age"],
    }

    refill = profile_data.get("refill")
    if refill:
        logging.info("refill: %s. Deleting profile..", refill)

        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{cfg.profile_service_url}/profiles/{profile_data['user_id']}")
            logging.info("Deletion status: %d; data: %s", response.status_code, response.json())

        await state.update_data(
            refill=None,
        )

    print('Trying to create profile...')
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            form_data_str = {k: str(v) for k, v in new_profile_data.items()}
            print('Form data:', form_data_str)

            files = []
            if len(photo_file_bytes) > 0:
                for i, photo_bytes in enumerate(photo_file_bytes):
                    # Each file is a tuple: (field_name, (filename, content, content_type))
                    files.append(("photos", (f"profile_photo_{i + 1}.jpg", photo_bytes, "image/jpeg")))

            response = await client.post(
                cfg.profile_service_url + '/profiles',
                data=form_data_str,
                files=files
            )
            print('Create profile resp:', response.json())

            if response.status_code not in (200, 201):
                logging.error(f"Ошибка при создании анкеты: {response.status_code} {response.text}")
                await message.answer(f"❌ Произошла ошибка при создании анкеты: {response.status_code} {response.text}")
                return

            try:
                if refill:
                    rating_response = await client.put(
                        cfg.rating_service_url + '/ratings',
                        json=new_profile_data
                    )
                else:
                    rating_response = await client.post(
                        cfg.rating_service_url + '/ratings',
                        json=new_profile_data
                    )

                rating_info = rating_response.json()
                new_preferences_data["rating"] = rating_info["rating_score"]

                if rating_response.status_code not in (200, 201):
                    logging.warning(
                            f"Не удалось создать рейтинг: {rating_response.status_code} {rating_response.text}")
            except Exception as e:
                logging.error(f"Ошибка при создании рейтинга: {e}")

            try:
                if refill:
                    user_id = new_preferences_data['user_id']
                    del new_preferences_data['user_id']
                    matching_response = await client.put(
                        cfg.matching_service_url + f"/users/info/{user_id}",
                        json=new_preferences_data
                    )
                else:
                    matching_response = await client.post(
                        cfg.matching_service_url + "/users/info",
                        json=new_preferences_data
                    )

                if matching_response.status_code not in (200, 201):
                    logging.warning(
                        f"Не удалось создать предпочтения: {matching_response.status_code} {matching_response.text}")
            except Exception as e:
                logging.error(f"Ошибка при создании предпочтения: {e}")

            if response.status_code not in (200, 201):
                await message.answer(f"❌ Произошла ошибка при создании анкеты: {response.status_code} {response.text}")
                return

            await message.answer(
                "✅ Ваша анкета успешно создана! Можете начать просмотр других анкет командой /view")
            await state.clear()
    except httpx.RequestError as e:
        await message.answer(f"❌ Ошибка сети при создании анкеты: {e}")
    except Exception as e:
        await message.answer(f"❌ Непредвиденная ошибка при создании анкеты: {e}")
        await state.clear()


async def load_suitable_profiles(message: types.Message, offset: int, cfg: Config):
    current_user_id = message.chat.id
    match_profiles_url = f"{cfg.matching_service_url}/match/profiles/{current_user_id}?offset={offset}&limit=50"

    async with httpx.AsyncClient() as client:
        response = await client.get(match_profiles_url)

        if response.status_code == 200:
            profiles_data = response.json()

            return profiles_data
        elif response.status_code == 404:
            return []
        raise Exception(f"{response.json()}")


async def show_next_profile(message: types.Message, state: FSMContext, cfg: Config):
    current_user_id = message.chat.id
    data = await state.get_data()

    try:
        profiles_data = data.get('matched_profiles')
        last_loaded = data.get('last_loaded')
        offset = data.get('matched_profiles_offset', 0)
        viewing_profile_idx = data.get('viewing_profile_idx')

        print(profiles_data, last_loaded, offset,viewing_profile_idx)

        if (profiles_data is None) or (last_loaded is not None and (datetime.now() - datetime.fromisoformat(last_loaded) > timedelta(minutes=1))):
            profiles_data = await load_suitable_profiles(message, offset, cfg)
            if len(profiles_data) == 0:
                await state.clear()
                await message.answer("🤷‍♀️ Анкеты для просмотра закончились. Попробуйте позже.", reply_markup=remove_kb)
                return

            viewing_profile_idx = 0

            await state.update_data(
                matched_profiles=profiles_data,
                matched_profiles_offset=viewing_profile_idx,
                viewing_profile_idx=viewing_profile_idx,
                last_loaded=datetime.now()
            )

        if viewing_profile_idx >= len(profiles_data):
            await state.set_state(None)
            await message.answer("🤷‍♀️ Анкеты для просмотра закончились. Попробуйте позже.", reply_markup=remove_kb)
            return

        current_profile = profiles_data[viewing_profile_idx]

        await state.update_data(
            viewing_profile_id=current_profile['id'],
            viewing_profile_username=current_profile['tg_username'],
            view_offset=data.get('view_offset', 0) + 1
        )
        await state.set_state(ViewingStates.viewing)

        keyboard = get_rating_keyboard()
        await send_view_profile_msg(current_profile, message, keyboard)
    except Exception as e:
        await state.clear()
        await message.answer(f"😕 Не удалось загрузить анкеты. Ошибка: {e}",
                             reply_markup=remove_kb)


async def send_view_profile_msg(current_profile, message, keyboard):
    caption = (
        f"<b>{current_profile['first_name']} {current_profile.get('last_name', '')}, {current_profile['age']}</b>, {current_profile['city']}\n"
        f"Пол: {'М' if current_profile['gender'] == 'male' else 'Ж'}\n\n"
        f"{'О себе: ' + current_profile.get('bio') if current_profile.get('bio') != '' else 'Нет описания'}"
    )

    photo_file_ids = current_profile.get('photo_file_ids')
    if photo_file_ids and photo_file_ids != "None":
        logging.info(current_profile['photo_file_ids'])

        if len(photo_file_ids) == 1:
            await message.answer_photo(
                photo=current_profile['photo_file_ids'][0],
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            return

        await message.answer_media_group(
            media=[
                types.input_media_photo.InputMediaPhoto(
                    media=photo_id,
                    caption=caption if (i == len(photo_file_ids) - 1) else None,
                    parse_mode="HTML" if (i == len(photo_file_ids) - 1) else None,
                )
                for i, photo_id in enumerate(photo_file_ids)
            ],
        )
        await message.answer(
            "Меню",
            reply_markup=keyboard
        )

    else:
        await message.answer_photo(
            photo=DEFAULT_PROFILE_PHOTO_ID,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )


@router.message(Command("view"), StateFilter(None))
async def view_profiles_command(message: types.Message, state: FSMContext, cfg: FromDishka[Config]):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{cfg.profile_service_url}/profiles/{message.from_user.id}")
        if response.status_code == 200:
            await message.answer("Начинаем просмотр анкет...")
            await show_next_profile(message, state, cfg)
        elif response.status_code == 404:
            await message.answer("Сначала вам нужно создать свою анкету. Введите /start")
        else:
            await message.answer(f"Не удалось проверить вашу анкету. Ошибка: {response.status_code}")



@router.callback_query(StateFilter(ViewingStates.viewing), F.data.startswith("rate:"))
async def process_rating_callback(callback: types.CallbackQuery, state: FSMContext, cfg: FromDishka[Config]):
    action = callback.data.split(":")[1]
    current_user_id = callback.from_user.id
    state_data = await state.get_data()
    viewing_profile_id = state_data.get('viewing_profile_id')
    viewing_profile_username = state_data.get('viewing_profile_username')

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

    payload = {
        "rater_user_id": current_user_id,
        "rated_user_id": viewing_profile_id
    }

    try:
        async with httpx.AsyncClient() as client:
            rating_response = await client.post(
                f"{cfg.rating_service_url}/ratings/{action}",
                json=payload
            )

        if rating_response.status_code == 200:
            async with httpx.AsyncClient() as client:
                matching_response = await client.post(
                    f"{cfg.matching_service_url}/match/check",
                    json={
                        "rater_user_id": current_user_id,
                        "rated_user_id": viewing_profile_id,
                        "rater_username": callback.from_user.username,
                        "rated_username": viewing_profile_username,
                        "like_type": action
                    }
                )
                print('Matching response:', matching_response.json())

            if matching_response.status_code == 200:
                await callback.answer(f"Вы поставили {('лайк' if action == 'like' else 'дизлайк')}!")
            else:
                print('Error:', matching_response.json())
            # Показать следующую анкету
            await state.update_data(
                viewing_profile_idx=state_data.get('viewing_profile_idx') + 1
            )
            await show_next_profile(callback.message, state, cfg)
        else:
            await callback.answer(f"Ошибка при отправке оценки: {rating_response.status_code}", show_alert=True)
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
async def get_my_profile(message: types.Message, cfg: FromDishka[Config]):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{cfg.profile_service_url}/profiles/{message.from_user.id}")

        if response.status_code == 200:
            profile_data = response.json()
            keyboard = get_my_profile_keyboard()
            await send_view_profile_msg(profile_data, message, keyboard)
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

@router.callback_query(F.data == 'my_profile-delete')
async def fill_profile_again(callback: types.CallbackQuery, state: FSMContext, cfg: FromDishka[Config]):
    async with httpx.AsyncClient() as client:
        response = await client.delete(url=cfg.profile_service_url + f"/profiles/{callback.from_user.id}")
        if response.status_code not in (200, 204):
            logging.error('Something went wrong: %s', response.json())
            await callback.message.answer('Что-то пошло не так, попробуйте позже')
            return

    await state.clear()

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Вы удалили свою анкету. Если захотите заполнить снова, нажмите /start",
        parse_mode="HTML",
    )


@router.callback_query(F.data == 'my_profile-stats')
async def get_my_profile_stats(callback: types.CallbackQuery, cfg: FromDishka[Config]):
    async with httpx.AsyncClient() as client:
        response = await client.post(url=cfg.rating_service_url + f"/stats/info/{callback.from_user.id}")
        if response.status_code not in (200, 204):
            logging.error('Something went wrong: %s', response.json())
            await callback.message.answer('Что-то пошло не так, попробуйте позже')
            return

    stats_data = response.json()

    text = (
        "📊Статистика анкеты\n\n"
        f'Диалогов начато: {stats_data["chats_count"]}\n'
        f'Лайков получено: {stats_data["likes_received"]}\n'
        f'Лайков отправлено: {stats_data["likes_given"]}\n'
        f'Всего мэтчей: {stats_data["matches_count"]}\n'
        f'Приглашенных друзей: {stats_data["refs_count"]}'
    )

    if callback.message.caption:
        return await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text='Назад', callback_data='my_profile-stats-back')]
                ])
        )
    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data='my_profile-stats-back')]
        ])
    )


@router.callback_query(F.data == 'my_profile-stats-back')
async def back_to_profile(callback: types.CallbackQuery, cfg: FromDishka[Config]):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{cfg.profile_service_url}/profiles/{callback.from_user.id}")

        if response.status_code != 200:
            await callback.message.answer(f"Что-то пошло не так. Ошибка: {response.status_code}")
            return

    keyboard = get_my_profile_keyboard()
    if callback.message.text or callback.message.caption is None:
        await callback.message.edit_text(
            text='Меню',
            reply_markup=keyboard
        )
        return


    current_profile = response.json()
    caption = (
        f"<b>{current_profile['first_name']} {current_profile.get('last_name', '')}, {current_profile['age']}</b>, {current_profile['city']}\n"
        f"Пол: {'М' if current_profile['gender'] == 'male' else 'Ж'}\n\n"
        f"{'О себе: ' + current_profile.get('bio') if current_profile.get('bio') != '' else 'Нет описания'}"
    )
    await callback.message.edit_caption(
        caption=caption,
        parse_mode='HTML',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("show_username"))
async def show_username_in_match(callback: types.CallbackQuery, cfg: FromDishka[Config]):
    watcher_id = callback.from_user.id
    watched_id = callback.data.split(':')[1]

    async with httpx.AsyncClient() as client:
        watched_user_profile_resp = await client.get(cfg.profile_service_url + f"/profiles/{watched_id}")
        if watched_user_profile_resp.status_code != 200:
            logging.warning('Something went wrong during watched user profile retrieving: %s', watched_user_profile_resp.json())
            return

        dialog_rating_response = await client.post(
            cfg.rating_service_url + '/stats/chat',
            json={
                'watcher_id': watcher_id,
                'watched_id': watched_id,
            }
        )
        if dialog_rating_response.status_code != 200:
            logging.warning('Update rating when opening dialog failed: %s', dialog_rating_response.json())

    watcher_user_profile = watched_user_profile_resp.json()
    username = watcher_user_profile['tg_username']

    if callback.message.caption:
        await callback.message.ed
        it_caption(caption=callback.message.caption + f'\n\nНаписать: @{username}')
        return
    await callback.message.edit_text(text=callback.message.text + f'\n\nНаписать: @{username}')


@router.callback_query(F.data.startswith("my_likers"))
async def show_username_in_match(callback: types.CallbackQuery, state: FSMContext, bot: Bot, cfg: FromDishka[Config]):
    liker_ids = eval(callback.data.split('-')[1])
    await state.update_data(
        current_likers=liker_ids
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Начинаем просмотр анкет лайкеров...")
    await show_next_liker_profile(callback.message, callback.from_user.id, state, bot, cfg)


@router.callback_query(StateFilter(ViewingLikerProfiles.viewing), F.data.startswith("rate_liker:"))
async def process_rating_callback(callback: types.CallbackQuery, state: FSMContext, bot: Bot, cfg: FromDishka[Config]):
    action = callback.data.split(":")[1]
    current_user_id = callback.from_user.id
    state_data = await state.get_data()

    current_likers = state_data['current_likers']
    current_liker_idx = state_data.get('current_liker_idx', 0)
    current_liker_id = current_likers[current_liker_idx]

    await callback.message.edit_reply_markup(reply_markup=None)

    if action == "stop":
        await callback.message.answer("Просмотр анкет завершен.", reply_markup=remove_kb)
        await state.clear()
        await callback.answer()
        return

    try:
        async with httpx.AsyncClient() as client:
            liker_profile = await client.get(
                cfg.profile_service_url + f"/profiles/{current_liker_id}"
            )
            liker_profile_data = liker_profile.json()
            logging.debug('Profile response:', liker_profile_data)


            rating_response = await client.post(
                f"{cfg.rating_service_url}/ratings/{action}",
                json={
                    "rater_user_id": current_user_id,
                    "rated_user_id": current_liker_id
                }
            )
            matching_response = await client.post(
                f"{cfg.matching_service_url}/match/check",
                json={
                    "rater_user_id": current_user_id,
                    "rated_user_id": current_liker_id,
                    "rater_username": callback.from_user.username,
                    "rated_username": liker_profile_data['tg_username'],
                    "like_type": action
                }
            )
            logging.debug('Matching response:', matching_response.json())

        if rating_response.status_code == 200:
            await callback.answer(f"Вы поставили {('лайк' if action == 'like' else 'дизлайк')}!")

            # Показать следующую анкету
            await state.update_data(
                current_liker_idx=current_liker_idx + 1
            )
            await show_next_liker_profile(callback.message, current_user_id, state, bot, cfg)
        else:
            await callback.answer(f"Ошибка при отправке оценки: {rating_response.status_code}", show_alert=True)
            await callback.message.answer("Не удалось обработать ваш голос. Попробуйте позже.")
            print(rating_response.json())
            await state.clear()

    except httpx.RequestError as e:
        await callback.answer(f"Ошибка сети: {e}", show_alert=True)
        await callback.message.answer("Ошибка сети. Попробуйте позже.")
        await state.clear()
    except Exception as e:
        await callback.answer(f"Непредвидённая ошибка: {e}", show_alert=True)
        await callback.message.answer("Что-то пошло не так.")
        await state.clear()


async def show_next_liker_profile(message, liked_id, state, bot, cfg):
    data = await state.get_data()

    try:
        current_likers = data.get('current_likers')
        current_liker_idx = data.get('current_liker_idx', 0)

        if current_liker_idx >= len(current_likers):
            await state.clear()
            await message.answer('Лайки закончились')
            return

        current_liker_id = current_likers[current_liker_idx]
        async with httpx.AsyncClient() as client:
            liker_profile_resp = await client.get(f"{cfg.profile_service_url}/profiles/{current_liker_id}")
            liker_data = liker_profile_resp.json()
        print(liker_data)
        await send_like_msg(liker_data, bot, liked_id)

        await state.set_state(ViewingLikerProfiles.viewing)
    except Exception as e:
        print(e)
        await state.clear()
        await message.answer(f"😕 Не удалось загрузить анкеты. Ошибка: {e}",
                             reply_markup=remove_kb)


async def send_like_msg(liker_data, bot: Bot, liked_id):
    liker_profile_photos = liker_data['photo_file_ids']
    keyboard = get_rate_likers_keyboard()

    text = (
        f"❤️Поздравляем, y вас лайк от @{liker_data['tg_username']}!\n\n"
        f"<b>{liker_data['first_name']} {liker_data.get('last_name', '')}, {liker_data['age']}</b>, {liker_data['city']}\n"
        f"Пол: {'М' if liker_data['gender'] == 'male' else 'Ж'}\n\n"
        f"{'О себе: ' + liker_data.get('bio') if liker_data.get('bio') != '' else 'Нет описания'}"
    )

    if liker_profile_photos in ('None', None) or len(liker_profile_photos) <= 1:
        print(text, liker_profile_photos)
        await bot.send_photo(
            chat_id=liked_id,
            photo=DEFAULT_PROFILE_PHOTO_ID if (liker_profile_photos in ('None', None) or len(liker_profile_photos) == 0) else liker_data['photo_file_ids'][0],
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await bot.send_media_group(
            chat_id=liked_id,
            media=[
                types.input_media_photo.InputMediaPhoto(
                    media=photo_id,
                    caption=text if (i == len(liker_profile_photos) - 1) else None,
                    parse_mode="HTML" if (i == len(liker_profile_photos) - 1) else None,
                )
                for i, photo_id in enumerate(liker_profile_photos)
            ],
        )
        await bot.send_message(chat_id=liked_id, text='Меню', reply_markup=keyboard)


@router.message(F.content_type == 'photo')
async def get_photo(message: types.Message):
    print(message.photo[-1].file_id)
