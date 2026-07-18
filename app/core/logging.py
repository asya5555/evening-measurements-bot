import logging


class PersonalDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = record.msg.replace("OPENAI_API_KEY", "OPENAI_API_KEY_MASKED")
            record.msg = record.msg.replace("TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN_MASKED")
        return True


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger().addFilter(PersonalDataFilter())
