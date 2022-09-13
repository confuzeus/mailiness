import bcrypt
import sqlite3
import unittest
from unittest import TestCase

from rich.table import Table

from mailiness import settings
from mailiness.repo import DomainRepository, UserRepository, AliasRepository


class DomainRepositoryTest(TestCase):
    def setUp(self):
        db_conn = sqlite3.connect(":memory:")
        self.repo = DomainRepository(conn=db_conn)
        self.repo.cursor.execute(
            f"CREATE TABLE {settings.DOMAINS_TABLE_NAME}(name TEXT)"
        )

    def tearDown(self):
        self.repo.cursor.execute(f"DROP TABLE {settings.DOMAINS_TABLE_NAME}")

    def test_index_returns_data_in_correct_format(self):

        self.repo.cursor.execute("INSERT INTO domains VALUES(?)", ["example.com"])
        self.repo.db_conn.commit()

        data = self.repo.index(pretty=False)

        self.assertIsInstance(data["headers"], tuple)
        self.assertIn("example.com", data["rows"][0])

        pretty_data = self.repo.index()
        self.assertIsInstance(pretty_data, Table)

    def test_create_adds_domain_to_db_and_returns_correct_format(self):
        data = self.repo.create("example.org", pretty=False)
        self.assertIsInstance(data["headers"], tuple)
        self.assertIn("example.org", data["rows"][0])
        pretty_data = self.repo.create("example.net")
        self.assertIsInstance(pretty_data, Table)

        domains = self.repo.index(pretty=False)
        self.assertIn("example.org", domains["rows"][0])

    def test_edit_domain_name_updates_data_and_returns_correct_format(self):
        self.repo.create("example.org")
        data = self.repo.edit("name", "example.org", "example.net", pretty=False)
        self.assertIsInstance(data["headers"], tuple)
        self.assertIn("example.net", data["rows"][0])
        domains = self.repo.index(pretty=False)
        self.assertIn("example.net", domains["rows"][0])
        pretty_data = self.repo.edit("name", "example.net", "example.org")
        self.assertIsInstance(pretty_data, Table)

    def test_delete_domain_name(self):
        name = "example.org"
        self.repo.create(name)
        domains = self.repo.index(pretty=False)
        self.assertIn(name, domains["rows"][0])

        self.repo.delete(name)
        domains = self.repo.index(pretty=False)
        self.assertEqual(len(domains["rows"]), 0)


class UserRepositoryTest(TestCase):
    def setUp(self):
        db_conn = sqlite3.connect(":memory:")
        self.repo = UserRepository(conn=db_conn)
        self.repo.cursor.execute(
            f"CREATE TABLE {settings.DOMAINS_TABLE_NAME}(name TEXT)"
        )
        self.repo.cursor.execute(
            f"CREATE TABLE {settings.USERS_TABLE_NAME}(domain_id INTEGER, email TEXT, password TEXT, quota TEXT, FOREIGN KEY(domain_id) REFERENCES {settings.DOMAINS_TABLE_NAME}(rowid))"
        )
        self.domain_repo = DomainRepository(conn=db_conn)

    def test_index_return_data_in_correct_format(self):
        for data in (
            ("smith.com", (1, "john@smith.com", "secret", 2)),
            ("doe.com", (2, "jane@doe.com", "alsosecret", 3)),
        ):
            domain, user_data = data

            self.domain_repo.create(domain)
            self.repo.cursor.execute(
                f"INSERT INTO {settings.USERS_TABLE_NAME} VALUES (?, ?, ?, ?)",
                user_data,
            )
            self.repo.db_conn.commit()

        data = self.repo.index(pretty=False)
        self.assertIn("john@smith.com", data["rows"][0])
        self.assertIn("jane@doe.com", data["rows"][1])

        data = self.repo.index(domain="smith.com", pretty=False)
        self.assertIn("john@smith.com", data["rows"][0])
        self.assertEqual(len(data["rows"]), 1)

    def test_create_add_to_db_and_returns_correct_format(self):
        data = self.repo.index(pretty=False)
        self.assertEqual(len(data["rows"]), 0)

        self.domain_repo.create("smith.com")

        data = self.repo.create("john@smith.com", "secret", 2, pretty=False)
        self.assertEqual(int(data["rows"][0][2]), 2_000_000_000)

        data = self.repo.index(pretty=False)
        self.assertIn("john@smith.com", data["rows"][0])

        result = self.repo.cursor.execute(
            f"SELECT password FROM {settings.USERS_TABLE_NAME} WHERE email='john@smith.com'"
        )
        row = result.fetchone()
        _, password_hash = row[0].split(settings.PASSWORD_HASH_PREFIX)
        self.assertNotEqual(password_hash, "secret")
        self.assertTrue(bcrypt.checkpw(b"secret", password_hash.encode("utf-8")))

    def test_edit_updates_data_in_db(self):
        self.domain_repo.create("smith.com")
        target = "john@smith.com"
        self.repo.create(target, "secret", 2)

        self.repo.edit(target, password="password")

        result = self.repo.cursor.execute(
            f"SELECT password FROM {settings.USERS_TABLE_NAME} WHERE email=?", [target]
        )
        row = result.fetchone()
        _, password_hash = row[0].split(settings.PASSWORD_HASH_PREFIX)
        self.assertFalse(bcrypt.checkpw(b"secret", password_hash.encode("utf-8")))
        self.assertTrue(bcrypt.checkpw(b"password", password_hash.encode("utf-8")))

        self.repo.edit(target, quota=1)

        result = self.repo.cursor.execute(
            f"SELECT quota FROM {settings.USERS_TABLE_NAME} WHERE email=?", [target]
        )
        row = result.fetchone()
        self.assertEqual(int(row[0]), 1_000_000_000)

        new_email = "yung@smith.com"

        self.repo.edit(target, new_email=new_email)

        result = self.repo.cursor.execute(
            f"SELECT email FROM {settings.USERS_TABLE_NAME} WHERE email=?", [new_email]
        )
        row = result.fetchone()
        self.assertEqual(len(row), 1)

    def test_delete(self):
        self.domain_repo.create("smith.com")
        self.repo.create("john@smith.com", "secret", 2)

        data = self.repo.index(pretty=False)
        self.assertEqual(len(data["rows"]), 1)

        self.repo.delete("john@smith.com")
        data = self.repo.index(pretty=False)
        self.assertEqual(len(data["rows"]), 0)


class AliasRepositoryTest(TestCase):
    def setUp(self):
        db_conn = sqlite3.connect(":memory:")
        self.db_conn = db_conn
        self.repo = AliasRepository(conn=db_conn)
        self.repo.cursor.execute(
            f"CREATE TABLE {settings.DOMAINS_TABLE_NAME}(name TEXT)"
        )
        self.repo.cursor.execute(
            f"CREATE TABLE {settings.ALIASES_TABLE_NAME}(domain_id INTEGER, from_address TEXT, to_address TEXT, FOREIGN KEY(domain_id) REFERENCES domains(rowid))"
        )
        self.domain_repo = DomainRepository(conn=db_conn)
        self.domain_name = "smith.com"
        domain_data = self.domain_repo.create(self.domain_name, pretty=False)
        self.domain_id = domain_data["rows"][0][0]

    def test_index_returns_data_in_correct_format(self):
        from_address = "admin@smith.com"
        to_address = "john@doe.com"
        self.repo.cursor.execute(
            f"INSERT INTO {settings.ALIASES_TABLE_NAME} VALUES (?, ?, ?)",
            [
                self.domain_id,
                from_address,
                to_address,
            ],
        )
        self.db_conn.commit()

        data = self.repo.index(pretty=False)
        self.assertIn(from_address, data["rows"][0])

        domain_data = self.domain_repo.create("gmail.com", pretty=False)
        domain_id = domain_data["rows"][0][0]

        self.repo.cursor.execute(
            f"INSERT INTO {settings.ALIASES_TABLE_NAME} VALUEs (?,?,?)",
            [
                domain_id,
                "john@gmail.com",
                "john@smith.com",
            ],
        )

        self.db_conn.commit()
        data = self.repo.index(domain="gmail.com", pretty=False)

        self.assertEqual(len(data["rows"]), 1)
        self.assertIn("john@gmail.com", data["rows"][0])

    def test_create_add_to_db_and_returns_correct_format(self):
        from_address = "admin@" + self.domain_name
        to_address = "john@" + self.domain_name

        data = self.repo.create(from_address, to_address, pretty=False)
        self.assertIn(from_address, data['rows'])

        data = self.repo.index(pretty=False)
        self.assertIn(from_address, data['rows'][0])

if __name__ == "__main__":
    unittest.main()
