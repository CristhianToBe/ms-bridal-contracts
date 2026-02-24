import io
import zipfile
from pathlib import Path


def build_zip(artifacts: list[tuple[str | Path, str]]) -> io.BytesIO:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, archive_name in artifacts:
            zip_file.write(str(file_path), arcname=archive_name)
    zip_buffer.seek(0)
    return zip_buffer
