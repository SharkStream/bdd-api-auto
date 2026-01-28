from helpers.constants import RESOURCES
from pathlib import Path


def get_abs_file_path(pattern, elative_path=RESOURCES) -> str:
    if Path(pattern).is_file():
        return str(Path(pattern).resolve())
    found_files = [f for f in Path(elative_path).rglob(pattern) if f.is_file()]
    if len(found_files) > 1:
        raise Exception(f"Multiple files found for pattern {pattern} in {elative_path}: {found_files}")
    if len(found_files) == 0:
        raise Exception(f"No file found for pattern {pattern} in {elative_path}")
    return str(found_files[0].resolve())