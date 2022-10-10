from io import StringIO
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import bcrypt

from mailiness import g
from . import utils

test_config = utils.get_test_config()

g.config = test_config
g.debug = True
from mailiness import cli, dkim, repo  # noqa

mock_settings = MagicMock()
mock_settings.get_config.return_value = test_config


class CLITestCase(unittest.TestCase):
    def setUp(self):
        db_conn = sqlite3.connect(":memory:")
        self.db_conn = db_conn
        cursor = db_conn.cursor()
        self.cursor = cursor
        cursor.execute(
            f"CREATE TABLE {test_config['db']['domains_table_name']}(name TEXT NOT NULL UNIQUE)"
        )
        cursor.execute(
            f"CREATE TABLE {test_config['db']['users_table_name']}(domain_id INTEGER NOT NULL, email TEXT NOT NULL UNIQUE, password TEXT, quota INTEGER, FOREIGN KEY(domain_id) REFERENCES {test_config['db']['domains_table_name']}(rowid) ON DELETE CASCADE)"
        )
        cursor.execute(
            f"CREATE TABLE {test_config['db']['aliases_table_name']}(domain_id INTEGER NOT NULL, from_address TEXT NOT NULL UNIQUE, to_address TEXT NOT NULL, FOREIGN KEY(domain_id) REFERENCES {test_config['db']['domains_table_name']}(rowid) ON DELETE CASCADE)"
        )
        db_conn.commit()

    def tearDown(self):
        self.cursor.execute(f"DROP TABLE {test_config['db']['aliases_table_name']}")
        self.cursor.execute(f"DROP TABLE {test_config['db']['users_table_name']}")
        self.cursor.execute(f"DROP TABLE {test_config['db']['domains_table_name']}")
        self.db_conn.commit()


@patch('mailiness.cli.settings', mock_settings)
class DKIMInterfaceTest(unittest.TestCase):
    def test_save_dkim(self):
        domain_name = "smith.com"
        selector = "myselector"
        args = ["dkim", "keygen", "--save", "--quiet", domain_name, selector]

        with patch("mailiness.dkim.shutil"), patch("mailiness.dkim.subprocess"):
            dkim_maps_path = g.config['spam']['dkim_maps_path']
            dkim_private_key_dir = g.config['spam']['dkim_private_key_directory']

            cli.main(args)

            with open(dkim_maps_path, "r", encoding="utf-8") as fp:
                self.assertIn(domain_name, fp.read())

            pkey_file = Path(dkim_private_key_dir) / f"{domain_name}.{selector}.key"

            self.assertTrue(pkey_file.exists())


@patch('mailiness.cli.settings', mock_settings)
class DomainInterfaceTest(CLITestCase):
    def setUp(self):
        super().setUp()
        self.domain_name = "smith.com"
        self.domain_repo = repo.DomainRepository(conn=self.db_conn)

    def _get_domain_row(self):
        return self.cursor.execute(
            f"SELECT * FROM {test_config['db']['domains_table_name']}"
        )

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
        ) as mock_repo_class, patch("mailiness.dkim.shutil"), patch(
            "mailiness.dkim.subprocess"
        ):
            mock_repo_class.return_value = self.domain_repo
            dkim_maps_path = g.config["spam"]["dkim_maps_path"]
            dkim_private_key_dir = g.config["spam"]["dkim_private_key_directory"]

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

        with patch("mailiness.handlers.repo.DomainRepository") as mock_repo_class:
            mock_repo_class.return_value = self.domain_repo
            vmail_directory = g.config["mail"]["vmail_directory"]

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


@patch('mailiness.cli.settings', mock_settings)
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
                f"SELECT password FROM {test_config['db']['users_table_name']} WHERE email=?",
                [email],
            )

            row = result.fetchone()

            _, hashed_pw = row[0].split(test_config["users"]["password_hash_prefix"])

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
                f"SELECT password FROM {test_config['db']['users_table_name']} WHERE email=?",
                [email],
            )

            _, password_hash = result.fetchone()[0].split(
                test_config["users"]["password_hash_prefix"]
            )
            self.assertTrue(
                bcrypt.checkpw(
                    new_password.encode("utf-8"), password_hash.encode("utf-8")
                )
            )

    def test_user_list(self):
        args = ['user', 'list']

        self.user_repo.create("john@" + self.domain_name, 'password', 2)

        with patch("mailiness.handlers.repo.UserRepository") as user_repo_class, patch('sys.stdout', new=StringIO()) as fake_stdout:

            user_repo_class.return_value = self.user_repo

            cli.main(args)

            self.assertIn("john@" + self.domain_name, fake_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
