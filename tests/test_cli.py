import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mailiness import cli, settings


class CLITestCase(unittest.TestCase):
    def setUp(self):
        db_conn = sqlite3.connect(":memory:")
        self.db_conn = db_conn
        cursor = db_conn.cursor()
        self.cursor = cursor()
        cursor.execute(
            f"CREATE TABLE {settings.DOMAINS_TABLE_NAME}(name TEXT NOT NULL UNIQUE)"
        )
        cursor.execute(
            f"CREATE TABLE {settings.USERS_TABLE_NAME}(domain_id INTEGER NOT NULL, email TEXT NOT NULL UNIQUE, password TEXT, quota INTEGER, FOREIGN KEY(domain_id) REFERENCES {settings.DOMAINS_TABLE_NAME}(rowid) ON DELETE CASCADE)"
        )
        cursor.execute(
            f"CREATE TABLE {settings.ALIASES_TABLE_NAME}(domain_id INTEGER NOT NULL, from_address TEXT NOT NULL UNIQUE, to_address TEXT NOT NULL, FOREIGN KEY(domain_id) REFERENCES {settings.DOMAINS_TABLE_NAME}(rowid) ON DELETE CASCADE)"
        )
        db_conn.commit()

    def tearDown(self):
        self.cursor.execute(f"DROP TABLE {settings.ALIASES_TABLE_NAME}")
        self.cursor.execute(f"DROP TABLE {settings.USERS_TABLE_NAME}")
        self.cursor.execute(f"DROP TABLE {settings.DOMAINS_TABLE_NAME}")
        self.db_conn.commit()


class DKIMInterfaceTest(unittest.TestCase):
    def test_save_dkim(self):
        domain_name = "smith.com"
        selector = "myselector"
        args = ["dkim", "keygen", "--save", "--quiet", domain_name, selector]

        with patch("mailiness.dkim.settings") as mock_settings:

            with patch("mailiness.dkim.shutil") as mock_shutil:

                with patch("mailiness.dkim.subprocess") as mock_subprocess:
                    _, dkim_maps_path = tempfile.mkstemp()
                    dkim_private_key_dir = tempfile.mkdtemp()

                    mock_settings.DKIM_MAPS_PATH = dkim_maps_path
                    mock_settings.DKIM_PRIVATE_KEY_DIRECTORY = dkim_private_key_dir

                    mock_settings.RSA_PUBLIC_EXPONENT=65537
                    mock_settings.DKIM_KEY_SIZE=512

                    cli.main(args)

                    with open(dkim_maps_path, 'r', encoding='utf-8') as fp:
                        self.assertIn(domain_name, fp.read())

                    pkey_file = Path(dkim_private_key_dir) / f"{domain_name}.{selector}.key"

                    self.assertTrue(pkey_file.exists())

if __name__ == "__main__":
    unittest.main()
