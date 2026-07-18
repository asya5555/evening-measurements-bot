from datetime import UTC, datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    backlog_keyboard,
    confirmation_keyboard,
    delete_confirm_keyboard,
    missed_days_keyboard,
    sections_keyboard,
)
from app.bot.states import DeleteDataFlow, EntryFlow, Onboarding
from app.core.config import get_settings
from app.core.security import MinuteRateLimiter, is_allowed_user
from app.schemas.entry import DailyEntry
from app.schemas.settings import UserSettings
from app.services.analytics import daily_analysis, period_report
from app.services.date_utils import date_needs_clarification, observed_date_from_command, user_now
from app.services.extraction import heuristic_extract
from app.services.gaps import backlog_prompt, missed_days_prompt
from app.services.reminders import first_reminder_text
from app.services.summary import compact_entry_summary

router = Router()
settings = get_settings()
rate_limiter = MinuteRateLimiter(settings.request_rate_limit_per_minute)


async def guard(message: Message) -> bool:
    user_id = message.from_user.id if message.from_user else None
    username = message.from_user.username if message.from_user else None
    if not is_allowed_user(
        user_id,
        settings.telegram_allowed_user_ids,
        username=username,
        allowed_usernames=settings.telegram_allowed_usernames,
    ):
        await message.answer("Доступ к этому боту ограничен.")
        return False
    if user_id is not None and not rate_limiter.allow(user_id):
        await message.answer("Слишком много сообщений подряд. Попробуй чуть позже.")
        return False
    return True


@router.message(Command("start"))
async def start(message: Message, state: FSMContext) -> None:
    if not await guard(message):
        return
    await state.set_state(Onboarding.timezone)
    await message.answer(
        "Привет. Я буду помогать спокойно фиксировать вечерние наблюдения.\n"
        "Часовой пояс по умолчанию: Europe/Tbilisi. Напиши другой, если нужно, или отправь +."
    )


@router.message(Onboarding.timezone)
async def onboarding_timezone(message: Message, state: FSMContext) -> None:
    timezone = settings.default_timezone if message.text == "+" else (message.text or settings.default_timezone)
    await state.update_data(user_settings=UserSettings(timezone=timezone).model_dump())
    await state.set_state(Onboarding.first_reminder_time)
    await message.answer("Во сколько присылать первое напоминание? По умолчанию 13:00. Отправь + или своё время.")


@router.message(Onboarding.first_reminder_time)
async def onboarding_first_reminder_time(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    user_settings = UserSettings.model_validate(data["user_settings"])
    user_settings.first_reminder_time = "13:00" if message.text == "+" else (message.text or "13:00")
    await state.update_data(user_settings=user_settings.model_dump())
    await state.set_state(Onboarding.second_reminder_time)
    await message.answer("Во сколько присылать одно повторное напоминание? По умолчанию 18:00. Отправь + или своё время.")


@router.message(Onboarding.second_reminder_time)
async def onboarding_second_reminder_time(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    user_settings = UserSettings.model_validate(data["user_settings"])
    user_settings.second_reminder_time = "18:00" if message.text == "+" else (message.text or "18:00")
    await state.update_data(user_settings=user_settings.model_dump())
    await state.set_state(Onboarding.required_sections)
    await message.answer(
        "Какие разделы считать обязательными? Можно оставить стандартные: сон, отёки, вода, питание, активность, настроение. Отправь +."
    )


@router.message(Onboarding.required_sections)
async def onboarding_required(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    user_settings = UserSettings.model_validate(data["user_settings"])
    if message.text and message.text != "+":
        user_settings.required_sections = [part.strip() for part in message.text.split(",") if part.strip()]
    await state.update_data(user_settings=user_settings.model_dump())
    await state.clear()
    await message.answer(
        "Настройка завершена. Команды: /today, /yesterday, /add, /edit, /history, /week, /month, /export, /settings, /help."
    )


@router.message(Command("today", "yesterday"))
async def begin_entry(message: Message, state: FSMContext) -> None:
    if not await guard(message):
        return
    command = message.text.split()[0] if message.text else "/today"
    observed_on = observed_date_from_command(command, settings.default_timezone)
    await state.set_state(EntryFlow.collecting)
    await state.update_data(observed_on=observed_on.isoformat(), raw_messages=[])
    if command == "/today":
        await message.answer("Давай зафиксируем сегодняшний день. Можешь рассказать всё одним сообщением, голосом или частями.")
    else:
        await message.answer(first_reminder_text())


@router.message(EntryFlow.collecting, F.text)
async def collect_text(message: Message, state: FSMContext) -> None:
    if not await guard(message):
        return
    state_data = await state.get_data()
    raw_messages = [*state_data.get("raw_messages", []), message.text]
    if date_needs_clarification("\n".join(raw_messages), settings.default_timezone):
        await message.answer("Уточни, пожалуйста, к какой дате это относится?")
        return
    default_observed_on = datetime.fromisoformat(state_data["observed_on"]).date() if state_data.get("observed_on") else None
    required = UserSettings().required_sections
    extraction = heuristic_extract(
        "\n".join(raw_messages),
        timezone=settings.default_timezone,
        required_sections=required,
        today=user_now(settings.default_timezone).date(),
        default_observed_on=default_observed_on,
    )
    observed_on = extraction.observed_on or default_observed_on or observed_date_from_command("", settings.default_timezone)
    await state.update_data(
        raw_messages=raw_messages,
        observed_on=observed_on.isoformat(),
        structured_data=extraction.data.model_dump(mode="json"),
    )
    if extraction.clarification_questions:
        await state.set_state(EntryFlow.clarifying)
        await message.answer("Записала. Осталось уточнить:\n" + "\n".join(extraction.clarification_questions[:3]))
        return
    await state.set_state(EntryFlow.confirming)
    await message.answer(compact_entry_summary(observed_on, extraction.data), reply_markup=confirmation_keyboard())


@router.message(EntryFlow.clarifying, F.text)
async def clarify_text(message: Message, state: FSMContext) -> None:
    await state.set_state(EntryFlow.confirming)
    state_data = await state.get_data()
    raw_messages = [*state_data.get("raw_messages", []), message.text]
    default_observed_on = datetime.fromisoformat(state_data["observed_on"]).date() if state_data.get("observed_on") else None
    extraction = heuristic_extract(
        "\n".join(raw_messages),
        timezone=settings.default_timezone,
        required_sections=[],
        today=user_now(settings.default_timezone).date(),
        default_observed_on=default_observed_on,
    )
    observed_on = extraction.observed_on or default_observed_on or observed_date_from_command("", settings.default_timezone)
    await state.update_data(raw_messages=raw_messages, structured_data=extraction.data.model_dump(mode="json"))
    await message.answer(compact_entry_summary(observed_on, extraction.data), reply_markup=confirmation_keyboard())


@router.callback_query(F.data == "entry:confirm")
async def confirm_entry(callback: CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    data = state_data.get("structured_data", {})
    observed_on_text = state_data.get("observed_on", user_now(settings.default_timezone).date().isoformat())
    observed_on = datetime.fromisoformat(observed_on_text).date()
    analysis = daily_analysis(
        DailyEntry.model_validate(
            {
                "entry_date": observed_on,
                "observed_on": observed_on,
                "started_at": datetime.now(UTC),
                "status": "saved",
                "raw_messages": state_data.get("raw_messages", []),
                "data": data,
            }
        ).data,
        [],
        observed_on,
    )
    await state.clear()
    await callback.message.answer("Запись сохранена.\n\n" + analysis.summary + "\n" + analysis.reliability)
    await callback.answer()


@router.callback_query(F.data == "entry:save_no_analysis")
async def save_without_analysis(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Запись сохранена без аналитического комментария.")
    await callback.answer()


@router.callback_query(F.data == "entry:edit")
async def edit_entry(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(EntryFlow.editing)
    await callback.message.answer("Выбери раздел или напиши исправление свободным текстом.", reply_markup=sections_keyboard())
    await callback.answer()


@router.callback_query(F.data == "entry:add_more")
async def add_more(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(EntryFlow.collecting)
    await callback.message.answer("Хорошо, отправь дополнение.")
    await callback.answer()


@router.callback_query(F.data == "entry:cancel")
async def cancel_entry(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Заполнение отменено.")
    await callback.answer()


@router.message(Command("add", "edit"))
async def add_or_edit(message: Message, state: FSMContext) -> None:
    if not await guard(message):
        return
    await state.set_state(EntryFlow.adding)
    await message.answer("Напиши, что нужно добавить или исправить. Если дату не укажешь, я отнесу это ко вчерашней записи.")


@router.message(EntryFlow.adding, F.text)
async def add_or_edit_text(message: Message, state: FSMContext) -> None:
    if not await guard(message):
        return
    if date_needs_clarification(message.text or "", settings.default_timezone):
        await message.answer("Уточни, пожалуйста, к какой дате это относится?")
        return
    extraction = heuristic_extract(
        message.text or "",
        timezone=settings.default_timezone,
        required_sections=[],
        today=user_now(settings.default_timezone).date(),
    )
    observed_on = extraction.observed_on or observed_date_from_command("", settings.default_timezone)
    await state.clear()
    await message.answer(
        f"Поняла. Поищу запись за {observed_on.strftime('%d.%m.%Y')}. Если она есть — предложу изменение, если нет — создам новую запись."
    )


@router.message(Command("week"))
async def week(message: Message) -> None:
    if not await guard(message):
        return
    now = user_now(settings.default_timezone).date()
    report = period_report("week", now - timedelta(days=6), now, [])
    await message.answer(report.text)


@router.message(Command("month"))
async def month(message: Message) -> None:
    if not await guard(message):
        return
    now = user_now(settings.default_timezone).date()
    report = period_report("month", now - timedelta(days=29), now, [])
    await message.answer(report.text)


@router.message(Command("history"))
async def history(message: Message) -> None:
    if not await guard(message):
        return
    await message.answer("Последние записи будут показаны здесь после подключения базы данных.")


@router.message(Command("missing"))
async def missing_days(message: Message) -> None:
    if not await guard(message):
        return
    missing = [
        user_now(settings.default_timezone).date() - timedelta(days=2),
        user_now(settings.default_timezone).date() - timedelta(days=1),
    ]
    await message.answer(backlog_prompt(), reply_markup=backlog_keyboard())
    await message.answer(missed_days_prompt(missing), reply_markup=missed_days_keyboard())


@router.callback_query(F.data.startswith("missed:"))
async def missed_days_action(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data == "missed:start_next":
        observed_on = user_now(settings.default_timezone).date() - timedelta(days=2)
        await state.set_state(EntryFlow.collecting)
        await state.update_data(observed_on=observed_on.isoformat(), raw_messages=[])
        await callback.message.answer(f"Хорошо, начнём с {observed_on.strftime('%d.%m.%Y')}. Расскажи этот день.")
    elif callback.data == "missed:choose_date":
        await callback.message.answer("Напиши дату или естественно: сегодня, вчера, позавчера, в субботу.")
    else:
        await callback.message.answer("Хорошо, пропускаем. Можно вернуться позже.")
    await callback.answer()


@router.callback_query(F.data.startswith("backlog:"))
async def backlog_action(callback: CallbackQuery) -> None:
    if callback.data == "backlog:start":
        await callback.message.answer("Хорошо, начнём заполнять пропущенные дни по очереди.")
    elif callback.data == "backlog:tomorrow":
        await callback.message.answer("Хорошо, напомню завтра.")
    else:
        await callback.message.answer("Хорошо, пропускаем.")
    await callback.answer()


@router.message(Command("export"))
async def export(message: Message) -> None:
    if not await guard(message):
        return
    await message.answer("Экспорт подготовлю в CSV, XLSX и JSON. В локальном режиме нужны данные из базы.")


@router.message(Command("settings"))
async def bot_settings(message: Message) -> None:
    if not await guard(message):
        return
    await message.answer("Настройки: часовой пояс, время напоминания, обязательные разделы, отчёты и шкалы.")


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    if not await guard(message):
        return
    await message.answer(
        "/today — заполнить сегодня\n"
        "/yesterday — заполнить вчера\n"
        "/add — добавить информацию\n"
        "/edit — исправить запись\n"
        "/week и /month — отчёты\n"
        "/export — выгрузка\n"
        "/delete_my_data — удалить данные"
    )


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Текущий сценарий отменён.")


@router.message(Command("delete_my_data"))
async def delete_my_data(message: Message, state: FSMContext) -> None:
    if not await guard(message):
        return
    await state.set_state(DeleteDataFlow.first_confirm)
    await message.answer(
        "Это удалит дневник и настройки. Нужно двойное подтверждение.",
        reply_markup=delete_confirm_keyboard(1),
    )


@router.callback_query(F.data == "delete:confirm:1")
async def delete_first(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DeleteDataFlow.second_confirm)
    await callback.message.answer("Последнее подтверждение удаления.", reply_markup=delete_confirm_keyboard(2))
    await callback.answer()


@router.callback_query(F.data == "delete:confirm:2")
async def delete_second(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Данные пользователя удалены или помечены к удалению в текущем окружении.")
    await callback.answer()


@router.message(F.voice)
async def voice_message(message: Message) -> None:
    if not await guard(message):
        return
    await message.answer("Голосовое получено. В рабочем окружении я расшифрую его через OpenAI и добавлю к записи.")


@router.message(F.photo)
async def photo_message(message: Message) -> None:
    if not await guard(message):
        return
    await message.answer("Фото получено. В рабочем окружении я извлеку только видимую информацию и привяжу его к записи.")
