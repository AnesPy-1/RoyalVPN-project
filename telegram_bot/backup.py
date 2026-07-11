import sqlite3
import tempfile
from pathlib import Path


def resolve_backup_database_path(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parent.parent
    return root / "db.sqlite3"


def create_sqlite_backup(source_path: Path | None = None, target_dir: Path | None = None) -> Path:
    source = source_path or resolve_backup_database_path()
    if not source.exists():
        raise FileNotFoundError(f"Database file not found: {source}")

    directory = target_dir or Path(tempfile.gettempdir())
    directory.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(prefix="royalvpn-backup-", suffix=".sqlite3", dir=str(directory))
    import os

    os.close(fd)
    backup_path = Path(temp_path)

    source_conn = sqlite3.connect(source)
    target_conn = sqlite3.connect(backup_path)
    try:
        source_conn.backup(target_conn)
    finally:
        target_conn.commit()
        target_conn.close()
        source_conn.close()

    return backup_path
