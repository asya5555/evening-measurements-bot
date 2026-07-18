import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.schemas.entry import ExtractionResult

PROMPT_VERSION = "2026-07-16"


class OpenAIService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.prompts_dir = Path(__file__).resolve().parents[1] / "prompts"

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def extract_entry(self, text: str, required_sections: list[str]) -> ExtractionResult:
        schema = ExtractionResult.model_json_schema()
        response = await self.client.responses.create(
            model=self.settings.openai_text_model,
            input=[
                {"role": "system", "content": self._prompt("extraction_system.md")},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"text": text, "required_sections": required_sections},
                        ensure_ascii=False,
                    ),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "daily_entry_extraction",
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        payload = response.output_text
        try:
            return ExtractionResult.model_validate_json(payload)
        except ValidationError as exc:
            repaired = await self._repair_invalid_json(payload, str(exc), schema)
            return ExtractionResult.model_validate_json(repaired)

    async def analyze_image(self, image_base64: str, mime_type: str) -> dict[str, Any]:
        response = await self.client.responses.create(
            model=self.settings.openai_vision_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Опиши только наблюдаемое на фото еды, упаковки, этикетки или измерений. "
                        "Не придумывай вес, состав или калорийность."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image",
                            "image_url": f"data:{mime_type};base64,{image_base64}",
                        }
                    ],
                },
            ],
        )
        return {"observed": response.output_text}

    async def transcribe_audio(self, file_path: Path) -> str:
        with file_path.open("rb") as audio:
            result = await self.client.audio.transcriptions.create(
                model=self.settings.openai_transcription_model,
                file=audio,
            )
        return result.text

    async def _repair_invalid_json(self, payload: str, error: str, schema: dict[str, Any]) -> str:
        response = await self.client.responses.create(
            model=self.settings.openai_text_model,
            input=[
                {"role": "system", "content": "Исправь JSON так, чтобы он соответствовал схеме."},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"invalid_json": payload, "validation_error": error, "schema": schema},
                        ensure_ascii=False,
                    ),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "daily_entry_extraction",
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        return response.output_text

    def _prompt(self, name: str) -> str:
        return (self.prompts_dir / name).read_text(encoding="utf-8")
