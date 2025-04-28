from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, \
    KeyboardButton

gender_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Мужчина', callback_data='gender_male'),
        InlineKeyboardButton(text='Женщина', callback_data='gender_female')
    ]
])

skip_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Пропустить")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

remove_kb = ReplyKeyboardRemove()


def get_my_profile_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Статистика', callback_data='my_profile-stats'),
                InlineKeyboardButton(text='Заполнить заново', callback_data='my_profile-reset')
            ],
            [InlineKeyboardButton(text='Удалить', callback_data='my_profile-delete')]
        ]
    )


gender_preferences_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Мужчин', callback_data='gender_pref:male'),
        InlineKeyboardButton(text='Женщин', callback_data='gender_pref:female'),

    ],
    [InlineKeyboardButton(text='Все равно', callback_data='gender_pref:any')]
])


def get_rate_likers_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👍 Лайк", callback_data="rate_liker:like"),
                InlineKeyboardButton(text="👎 Дизлайк", callback_data="rate_liker:dislike"),
            ],
            [
                InlineKeyboardButton(text="❌ Закончить просмотр", callback_data="rate_liker:stop"),
            ]
        ]
    )


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
