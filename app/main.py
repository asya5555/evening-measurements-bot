import uvicorn

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run("app.api.app:app", host="0.0.0.0", port=8000, reload=settings.app_env == "local")


if __name__ == "__main__":
    main()
