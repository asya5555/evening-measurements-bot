from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DailyEntry, EntryVersion, RawMessage


class EntryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_date(self, user_id: int, observed_on: date) -> DailyEntry | None:
        result = await self.session.execute(
            select(DailyEntry).where(
                DailyEntry.user_id == user_id,
                DailyEntry.observed_on == observed_on,
            )
        )
        return result.scalar_one_or_none()

    async def create_or_update_draft(
        self,
        *,
        user_id: int,
        observed_on: date,
        entry_date: date,
        started_at: datetime,
        data: dict[str, Any],
        extraction: dict[str, Any],
        model_id: str | None,
        prompt_version: str | None,
    ) -> DailyEntry:
        entry = await self.get_by_date(user_id, observed_on)
        if entry is None:
            entry = DailyEntry(
                user_id=user_id,
                observed_on=observed_on,
                entry_date=entry_date,
                started_at=started_at,
                status="draft",
                structured_data=data,
                extraction_result=extraction,
                model_id=model_id,
                prompt_version=prompt_version,
            )
            self.session.add(entry)
        else:
            await self.snapshot(entry, "draft_update")
            entry.structured_data = data
            entry.extraction_result = extraction
            entry.status = "awaiting_confirmation"
        await self.session.flush()
        return entry

    async def snapshot(self, entry: DailyEntry, reason: str) -> None:
        count = len(entry.versions) if entry.versions else 0
        self.session.add(
            EntryVersion(
                entry_id=entry.id,
                version_number=count + 1,
                change_reason=reason,
                data_snapshot=entry.structured_data,
            )
        )

    async def add_raw_message(
        self,
        user_id: int,
        entry_id: int | None,
        telegram_message_id: int | None,
        message_type: str,
        redacted_text: str | None,
    ) -> None:
        self.session.add(
            RawMessage(
                user_id=user_id,
                entry_id=entry_id,
                telegram_message_id=telegram_message_id,
                message_type=message_type,
                redacted_text=redacted_text,
            )
        )
