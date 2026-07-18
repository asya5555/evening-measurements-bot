from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Всё верно", callback_data="entry:confirm"),
                InlineKeyboardButton(text="Исправить", callback_data="entry:edit"),
            ],
            [
                InlineKeyboardButton(text="Добавить ещё", callback_data="entry:add_more"),
                InlineKeyboardButton(text="Сохранить без анализа", callback_data="entry:save_no_analysis"),
            ],
            [InlineKeyboardButton(text="Отменить", callback_data="entry:cancel")],
        ]
    )


def sections_keyboard() -> InlineKeyboardMarkup:
    sections = [
        ("Сон", "sleep"),
        ("Отёки", "edema"),
        ("Вода", "drinks"),
        ("Питание", "nutrition"),
        ("Активность", "activity"),
        ("Настроение", "mood"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=f"section:{value}")] for label, value in sections]
    )


def delete_confirm_keyboard(step: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подтверждаю удаление",
                    callback_data=f"delete:confirm:{step}",
                )
            ],
            [InlineKeyboardButton(text="Отмена", callback_data="delete:cancel")],
        ]
    )


def missed_days_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="missed:start_next")],
            [InlineKeyboardButton(text="Пропустить", callback_data="missed:skip")],
            [InlineKeyboardButton(text="Выбрать другую дату", callback_data="missed:choose_date")],
        ]
    )


def backlog_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заполнить по очереди", callback_data="backlog:start")],
            [InlineKeyboardButton(text="Пропустить", callback_data="backlog:skip")],
            [InlineKeyboardButton(text="Напомнить завтра", callback_data="backlog:tomorrow")],
        ]
    )
