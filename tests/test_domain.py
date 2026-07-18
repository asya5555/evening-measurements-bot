import unittest
from datetime import UTC, date, datetime

from app.core.config import Settings
from app.core.security import MinuteRateLimiter, is_allowed_user, mask_secret
from app.schemas.entry import DailyEntryData
from app.services.analytics import period_report
from app.services.date_utils import date_needs_clarification, default_observed_date, infer_observed_date, observed_date_from_command
from app.services.extraction import estimate_cycle_phase, heuristic_extract
from app.services.gaps import missing_observed_dates
from app.services.reminders import build_daily_reminder_plan
from app.services.required_fields import clarification_questions, missing_required_sections
from app.services.summary import compact_entry_summary


class SecurityTests(unittest.TestCase):
    def test_allowed_user(self) -> None:
        self.assertTrue(is_allowed_user(42, [1, 42]))
        self.assertTrue(is_allowed_user(None, [], username="@asya5555", allowed_usernames=["asya5555"]))
        self.assertFalse(is_allowed_user(7, [1, 42]))
        self.assertFalse(is_allowed_user(None, [1, 42]))

    def test_render_database_url_is_normalized(self) -> None:
        settings = Settings(
            database_url="postgresql://user:password@example.com:5432/db",
            telegram_allowed_usernames="@asya5555",
        )
        self.assertEqual(settings.database_url, "postgresql+asyncpg://user:password@example.com:5432/db")
        self.assertEqual(settings.telegram_allowed_usernames, ["asya5555"])

    def test_mask_secret(self) -> None:
        self.assertEqual(mask_secret("sk-1234567890", visible=3), "sk-...890")

    def test_rate_limiter_blocks_after_limit(self) -> None:
        limiter = MinuteRateLimiter(limit=2)
        now = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
        self.assertTrue(limiter.allow(1, now))
        self.assertTrue(limiter.allow(1, now))
        self.assertFalse(limiter.allow(1, now))


class DateTests(unittest.TestCase):
    def test_observed_date_from_command(self) -> None:
        now = datetime(2026, 7, 16, 21, 0, tzinfo=UTC)
        self.assertEqual(observed_date_from_command("/today", "UTC", now), date(2026, 7, 16))
        self.assertEqual(observed_date_from_command("/yesterday", "UTC", now), date(2026, 7, 15))
        self.assertEqual(observed_date_from_command("", "UTC", now), date(2026, 7, 15))
        self.assertEqual(default_observed_date("UTC", now), date(2026, 7, 15))

    def test_infer_relative_date(self) -> None:
        now = datetime(2026, 7, 16, 21, 0, tzinfo=UTC)
        self.assertEqual(infer_observed_date("Это относилось ко вчерашнему дню", "UTC", now), date(2026, 7, 15))
        self.assertEqual(infer_observed_date("позавчера было плавание", "UTC", now), date(2026, 7, 14))
        self.assertEqual(infer_observed_date("Нет, это было уже сегодня", "UTC", now), date(2026, 7, 16))
        self.assertEqual(infer_observed_date("Это относится к субботе", "UTC", now), date(2026, 7, 11))
        self.assertTrue(date_needs_clarification("Сегодня добавь ко вчера", "UTC", now))


class ExtractionTests(unittest.TestCase):
    def test_extracts_core_fields_and_keeps_multiple_sleep_periods(self) -> None:
        result = heuristic_extract(
            "Спала с 3 до 8, потом ещё до 11. Была прогулка и короткая зарядка. "
            "Отёки на 3 из 10. Выпила литр воды и чай. Ела курицу, баклажан, яблоко. "
            "Стул нормальный. День цикла пятнадцатый. Настроение спокойное, концентрация очень высокая.",
            timezone="UTC",
            required_sections=["sleep", "edema", "drinks", "nutrition", "activity", "mood"],
            today=date(2026, 7, 16),
        )
        self.assertEqual(result.observed_on, date(2026, 7, 15))
        self.assertEqual(result.data.sleep.fell_asleep_at, "03:00")
        self.assertEqual(result.data.sleep.final_wake_at, "08:00")
        self.assertEqual(len(result.data.sleep.additional_periods), 1)
        self.assertEqual(result.data.edema.score, 3)
        self.assertEqual(result.data.drinks.pure_water_ml, 1000)
        self.assertEqual(result.data.drinks.tea_ml, 250)
        self.assertTrue(result.data.activity.walk)
        self.assertTrue(result.data.activity.exercise)
        self.assertEqual(result.data.digestion.stool, "нормальный")
        self.assertEqual(result.data.focus.score, 9)
        self.assertNotIn("sleep", result.missing_required_fields)

    def test_missing_questions_are_specific(self) -> None:
        data = DailyEntryData()
        missing = missing_required_sections(data, ["sleep", "edema", "mood"])
        self.assertEqual(missing, ["sleep", "edema", "mood"])
        questions = clarification_questions(missing)
        self.assertEqual(len(questions), 3)
        self.assertIn("отёки", questions[1])

    def test_cycle_phase_is_marked_calculated(self) -> None:
        self.assertEqual(estimate_cycle_phase(15), "овуляторная")


class ReportingTests(unittest.TestCase):
    def test_summary_contains_confirmation_sections(self) -> None:
        data = DailyEntryData()
        data.edema.score = 4
        text = compact_entry_summary(date(2026, 7, 16), data)
        self.assertIn("Отёки: 4/10", text)
        self.assertIn("Питание:", text)

    def test_period_report_does_not_claim_causality(self) -> None:
        report = period_report("week", date(2026, 7, 10), date(2026, 7, 16), [])
        self.assertIn("не доказанные причины", report.text)
        self.assertEqual(report.filled_days, 0)


class ReminderTests(unittest.TestCase):
    def test_reminder_plan_uses_timezone_and_idempotency(self) -> None:
        plan = build_daily_reminder_plan(123, date(2026, 7, 12), "13:00", "18:00", "Europe/Tbilisi")
        self.assertEqual(plan.notification_on, date(2026, 7, 13))
        self.assertEqual(plan.first_idempotency_key, "123:2026-07-12:first-reminder")
        self.assertEqual(plan.second_idempotency_key, "123:2026-07-12:second-reminder")
        self.assertLess(plan.first_for_utc, plan.second_for_utc)


class MissingDaysTests(unittest.TestCase):
    def test_missing_dates_do_not_create_empty_entries(self) -> None:
        missing = missing_observed_dates(
            date(2026, 7, 11),
            date(2026, 7, 13),
            {date(2026, 7, 13)},
        )
        self.assertEqual(missing, [date(2026, 7, 11), date(2026, 7, 12)])


if __name__ == "__main__":
    unittest.main()
