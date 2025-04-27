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
            [InlineKeyboardButton(text='Заполнить заново', callback_data='my_profile-reset')]
        ]
    )


gender_preferences_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Мужчин', callback_data='gender_pref:male'),
        InlineKeyboardButton(text='Женщин', callback_data='gender_pref:female'),

    ],
    [InlineKeyboardButton(text='Все равно', callback_data='gender_pref:any')]
])
