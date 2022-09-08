from rich.table import Table
import sqlite3
from unittest import TestCase

from mailiness.repo import DomainRepository


class DomainRepositoryTest(TestCase):
    def setUp(self):
        db_conn = sqlite3.connect(":memory:")
        self.repo = DomainRepository(conn=db_conn)
        self.repo.cursor.execute("CREATE TABLE domains(name TEXT)")

    def test_index_returns_data_in_correct_format(self):

        self.repo.cursor.execute("INSERT INTO domains VALUES(?)", ["example.com"])
        self.repo.db_conn.commit()

        data = self.repo.index(pretty=False)

        self.assertIsInstance(data["headers"], tuple)
        self.assertIn("example.com", data['rows'][0])

        pretty_data = self.repo.index()
        self.assertIsInstance(pretty_data, Table)


if __name__ == "__main__":
    unittest.main()
