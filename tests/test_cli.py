import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bcrypt

from mailiness import cli, dkim, repo, settings


class CLITestCase(unittest.TestCase):
    def setUp(self):
        db_conn = sqlite3.connect(":memory:")
        self.db_conn = db_conn
        cursor = db_conn.cursor()
        self.cursor = cursor
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

        with patch("mailiness.dkim.settings") as mock_settings, patch(
            "mailiness.dkim.shutil"
        ), patch("mailiness.dkim.subprocess"):
            _, dkim_maps_path = tempfile.mkstemp()
            dkim_private_key_dir = tempfile.mkdtemp()

            mock_settings.DKIM_MAPS_PATH = dkim_maps_path
            mock_settings.DKIM_PRIVATE_KEY_DIRECTORY = dkim_private_key_dir

            mock_settings.RSA_PUBLIC_EXPONENT = 65537
            mock_settings.DKIM_KEY_SIZE = 512

            cli.main(args)

            with open(dkim_maps_path, "r", encoding="utf-8") as fp:
                self.assertIn(domain_name, fp.read())

            pkey_file = Path(dkim_private_key_dir) / f"{domain_name}.{selector}.key"

            self.assertTrue(pkey_file.exists())


class DomainInterfaceTest(CLITestCase):
    def setUp(self):
        super().setUp()
        self.domain_name = "smith.com"
        self.domain_repo = repo.DomainRepository(conn=self.db_conn)

    def _get_domain_row(self):
        return self.cursor.execute(f"SELECT * FROM {settings.DOMAINS_TABLE_NAME}")

    def test_domain_add_adds_domain_to_db(self):
        args = ["domain", "add", self.domain_name]

        with patch("mailiness.handlers.repo.DomainRepository") as mock_repo_class:

            mock_repo_class.return_value = self.domain_repo

            cli.main(args)

        result = self._get_domain_row()

        row = result.fetchone()
        self.assertIn(self.domain_name, row)

    def test_domain_add_dkim_saves_dkim_key(self):

        args = ["domain", "add", self.domain_name, "--dkim", "--selector", "myselector"]

        with patch(
            "mailiness.handlers.repo.DomainRepository"
        ) as mock_repo_class, patch("mailiness.dkim.settings") as mock_settings, patch(
            "mailiness.dkim.shutil"
        ), patch(
            "mailiness.dkim.subprocess"
        ):
            mock_repo_class.return_value = self.domain_repo
            _, dkim_maps_path = tempfile.mkstemp()
            dkim_private_key_dir = tempfile.mkdtemp()

            mock_settings.DKIM_MAPS_PATH = dkim_maps_path
            mock_settings.DKIM_PRIVATE_KEY_DIRECTORY = dkim_private_key_dir

            mock_settings.RSA_PUBLIC_EXPONENT = 65537
            mock_settings.DKIM_KEY_SIZE = 512

            cli.main(args)

            with open(dkim_maps_path, "r", encoding="utf-8") as fp:
                self.assertIn(self.domain_name, fp.read())

            pkey_file = (
                Path(dkim_private_key_dir) / f"{self.domain_name}.myselector.key"
            )

            self.assertTrue(pkey_file.exists())

    def test_domain_edit_name_changes_name_in_db(self):
        args = ["domain", "edit", "name", self.domain_name, "example.com"]

        with patch("mailiness.handlers.repo.DomainRepository") as mock_repo_class:

            mock_repo_class.return_value = self.domain_repo
            self.domain_repo.create(self.domain_name)

            cli.main(args)

            result = self._get_domain_row()
            row = result.fetchone()
            self.assertIn("example.com", row)

    def test_domain_delete_removes_from_db(self):
        args = ["domain", "delete", self.domain_name, "--yes"]

        with patch("mailiness.handlers.repo.DomainRepository") as mock_repo_class:
            mock_repo_class.return_value = self.domain_repo
            self.domain_repo.create(self.domain_name)

            cli.main(args)

            result = self._get_domain_row()
            row = result.fetchone()
            self.assertIsNone(row)

    def test_domain_delete_mailbox_removes_mailbox_from_disk(self):
        args = ["domain", "delete", self.domain_name, "--yes", "--mailbox"]

        with patch(
            "mailiness.handlers.repo.DomainRepository"
        ) as mock_repo_class, patch("mailiness.handlers.settings") as mock_settings:
            mock_repo_class.return_value = self.domain_repo
            vmail_directory = tempfile.mkdtemp()
            mock_settings.VMAIL_DIRECTORY = vmail_directory

            mailbox_path = Path(vmail_directory) / self.domain_name
            mailbox_path.mkdir()

            self.domain_repo.create(self.domain_name)

            cli.main(args)

            self.assertFalse(mailbox_path.exists())

    def test_domain_delete_dkim_removes_dkim_keyfile_and_map_entry(self):
        args = ["domain", "delete", self.domain_name, "--yes", "--dkim"]
        selector = "myselector"
        _, dkim_maps_path = tempfile.mkstemp()
        dkim_private_key_dir = tempfile.mkdtemp()
        key = dkim.DKIM(self.domain_name, selector)
        key.dkim_maps_path = dkim_maps_path
        key.dkim_private_key_dir = dkim_private_key_dir
        with patch.object(dkim, "shutil"), patch.object(dkim, "subprocess"):
            key.save_private_key()

        dkim_map = key.load_from_dkim_map_file()
        self.assertIn(self.domain_name, dkim_map.keys())
        keyfile_path = Path(dkim_private_key_dir) / f"{self.domain_name}.{selector}.key"
        self.assertTrue(keyfile_path.exists())
        with patch(
            "mailiness.handlers.repo.DomainRepository"
        ) as mock_repo_class, patch(
            "mailiness.handlers.dkim.DKIM"
        ) as mock_dkim_class, patch(
            "mailiness.handlers.dkim.shutil"
        ), patch(
            "mailiness.handlers.dkim.subprocess"
        ):
            mock_repo_class.return_value = self.domain_repo
            self.domain_repo.create(self.domain_name)
            mock_dkim_class.return_value = key

            cli.main(args)

            self.assertFalse(keyfile_path.exists())

            dkim_map = key.load_from_dkim_map_file()
            self.assertNotIn(self.domain_name, dkim_map.keys())


class UserInterfaceTestCase(CLITestCase):
    def setUp(self):
        super().setUp()
        self.domain_name = "smith.com"
        self.domain_repo = repo.DomainRepository(conn=self.db_conn)
        self.domain_repo.create(self.domain_name)
        self.user_repo = repo.UserRepository(conn=self.db_conn)

    def test_user_add_adds_user_to_db(self):
        email = "john@" + self.domain_name
        password = "secret"
        quota = 2
        args = [
            "user",
            "add",
            email,
            str(quota),
            password,
        ]

        with patch("mailiness.handlers.repo.UserRepository") as user_repo_class:

            user_repo_class.return_value = self.user_repo

            cli.main(args)

            data = self.user_repo.index(pretty=False)

            self.assertIn(email, data["rows"][0])

    def test_user_add_random_password_saves_random_password(self):

        email = "john@" + self.domain_name

        password = "secret"

        quota = 2

        args = ["user", "add", email, str(quota), "--random-password"]

        with patch("mailiness.handlers.secrets") as mock_secrets, patch(
            "mailiness.handlers.repo.UserRepository"
        ) as user_repo_class:

            mock_secrets.token_urlsafe.return_value = password
            user_repo_class.return_value = self.user_repo

            cli.main(args)

            result = self.cursor.execute(
                f"SELECT password FROM {settings.USERS_TABLE_NAME} WHERE email=?",
                [email],
            )

            row = result.fetchone()

            _, hashed_pw = row[0].split(settings.PASSWORD_HASH_PREFIX)

            self.assertTrue(
                bcrypt.checkpw(password.encode("utf-8"), hashed_pw.encode("utf-8"))
            )

    def test_user_add_password_random_password_mutually_exclusive(self):
        email = "john@" + self.domain_name
        password = "secret"
        quota = 2
        args = ["user", "add", email, str(quota), password, "--random-password"]

        with self.assertRaises(SystemExit):
            cli.main(args)

    def test_user_edit_email_changes_email_in_db(self):

        email = "john@" + self.domain_name
        new_email = "joe@" + self.domain_name
        password = "secret"
        quota = 2
        args = ["user", "edit", email, "--new-email", new_email]

        self.user_repo.create(email, password, quota)

        with patch("mailiness.handlers.repo.UserRepository") as user_repo_class:

            user_repo_class.return_value = self.user_repo

            cli.main(args)

            data = self.user_repo.index(pretty=False)

            self.assertIn(new_email, data["rows"][0])

    def test_user_edit_password_changes_password_in_db(self):
        email = "john@" + self.domain_name
        password = "secret"
        new_password = "alsosecret"

        self.user_repo.create(email, password, 2)

        args = ["user", "edit", email, "--password", new_password]

        with patch("mailiness.handlers.repo.UserRepository") as user_repo_class:

            user_repo_class.return_value = self.user_repo

            cli.main(args)

            result = self.cursor.execute(
                f"SELECT password FROM {settings.USERS_TABLE_NAME} WHERE email=?", [email]
            )

            _, password_hash = result.fetchone()[0].split(settings.PASSWORD_HASH_PREFIX)
            self.assertTrue(bcrypt.checkpw(new_password.encode('utf-8'), password_hash.encode('utf-8')))


if __name__ == "__main__":
    unittest.main()
