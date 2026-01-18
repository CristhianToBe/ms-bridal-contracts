import os
from pathlib import Path
from dotenv import load_dotenv

def load_settings() -> dict:
    """
    Carga variables de entorno desde un archivo .env si existe y devuelve un dict con la configuración.
    """
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    return {
        "NOTION_TOKEN": os.getenv("NOTION_TOKEN"),
        "NOTION_DATABASE_ID": os.getenv("NOTION_DATABASE_ID"),
    }
