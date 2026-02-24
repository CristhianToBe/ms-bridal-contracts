from pathlib import Path


def get_repo_root(base_dir: str | Path) -> Path:
    return Path(base_dir).resolve().parent


def resolve_path(path_str: str, base: Path) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return base / path
