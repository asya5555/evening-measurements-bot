import csv
import json
from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook

from app.schemas.entry import DailyEntry


@dataclass(frozen=True)
class ExportBundle:
    csv_path: Path
    xlsx_path: Path
    json_path: Path


class ExportService:
    def __init__(self, export_dir: str) -> None:
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_entries(self, user_id: int, entries: list[DailyEntry]) -> ExportBundle:
        prefix = self.export_dir / f"user-{user_id}-diary"
        csv_path = prefix.with_suffix(".csv")
        xlsx_path = prefix.with_suffix(".xlsx")
        json_path = prefix.with_suffix(".json")
        self._write_csv(csv_path, entries)
        self._write_xlsx(xlsx_path, entries)
        json_path.write_text(
            json.dumps([entry.model_dump(mode="json") for entry in entries], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return ExportBundle(csv_path=csv_path, xlsx_path=xlsx_path, json_path=json_path)

    def _write_csv(self, path: Path, entries: list[DailyEntry]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["observed_on", "sleep", "edema", "water_ml", "mood", "focus"],
            )
            writer.writeheader()
            for entry in entries:
                data = entry.data
                writer.writerow(
                    {
                        "observed_on": entry.observed_on.isoformat(),
                        "sleep": data.sleep.total_duration_minutes,
                        "edema": data.edema.score,
                        "water_ml": data.drinks.pure_water_ml,
                        "mood": data.mood.description or data.mood.score,
                        "focus": data.focus.description or data.focus.score,
                    }
                )

    def _write_xlsx(self, path: Path, entries: list[DailyEntry]) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "дневные записи"
        sheet.append(["Дата", "Статус", "Сон", "Отёки", "Вода", "Настроение"])
        for entry in entries:
            data = entry.data
            sheet.append(
                [
                    entry.observed_on.isoformat(),
                    entry.status,
                    data.sleep.total_duration_minutes,
                    data.edema.score,
                    data.drinks.pure_water_ml,
                    data.mood.description or data.mood.score,
                ]
            )
        for title in ["сон", "питание", "активность", "настроение", "цикл", "симптомы", "измерения"]:
            workbook.create_sheet(title)
        workbook.save(path)
