import json
import uuid
from pathlib import Path


def save_json_from_text(json_text: str, media_root: str | Path, prefix: str) -> Path:
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON inválido: {error}") from error

    media_path = Path(media_root)
    media_path.mkdir(parents=True, exist_ok=True)

    file_path = media_path / f"{prefix}_{uuid.uuid4().hex}.json"
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(parsed, file, ensure_ascii=False, indent=2)

    return file_path


def safe_remove(path: str | Path) -> None:
    file_path = Path(path)
    if file_path.exists():
        file_path.unlink()
