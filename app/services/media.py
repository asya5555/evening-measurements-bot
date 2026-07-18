import base64
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.config import Settings


class MediaService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.media_dir = Path(settings.media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def validate_size(self, size: int) -> None:
        if size > self.settings.max_media_bytes:
            raise ValueError("Файл слишком большой для обработки.")

    def purge_after(self) -> datetime:
        return datetime.now(UTC) + timedelta(days=self.settings.media_retention_days)

    def encode_image(self, path: Path) -> str:
        return base64.b64encode(path.read_bytes()).decode("ascii")
