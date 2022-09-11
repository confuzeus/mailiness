import sqlite3
import unittest
from unittest import TestCase

from rich.table import Table

from mailiness import settings
from mailiness.repo import DomainRepository, UserRepository


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

    def test_index_return_data_in_correct_format(self):
        for data in (
            ("smith.com", (1, "john@smith.com", "secret", 2)),
            ("doe.com", (2, "jane@doe.com", "alsosecret", 3)),
        ):
            domain, user_data = data

            self.repo.cursor.execute(
                f"INSERT INTO {settings.DOMAINS_TABLE_NAME} VALUES (?)", [domain]
            )
            self.repo.db_conn.commit()
            self.repo.cursor.execute(
                f"INSERT INTO {settings.USERS_TABLE_NAME} VALUES (?, ?, ?, ?)", user_data
            )

        data = self.repo.index(pretty=False)
        self.assertIn("john@smith.com", data['rows'][0])
        self.assertIn("jane@doe.com", data['rows'][1])

        data = self.repo.index(domain="smith.com", pretty=False)
        self.assertIn("john@smith.com", data['rows'][0])
        self.assertEqual(len(data['rows']), 1)


if __name__ == "__main__":
    unittest.main()
