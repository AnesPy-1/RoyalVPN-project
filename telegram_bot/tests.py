import unittest
from pathlib import Path

from telegram_bot.backup import resolve_backup_database_path


class BackupPathTests(unittest.TestCase):
    def test_returns_repo_database_path(self):
        repo_root = Path(__file__).resolve().parent.parent
        self.assertEqual(resolve_backup_database_path(repo_root), repo_root / "db.sqlite3")


if __name__ == "__main__":
    unittest.main()
