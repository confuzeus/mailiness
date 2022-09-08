import sqlite3
from typing import Union
from rich.table import Table

from . import settings


def get_db_conn(dsn=settings.DB_CONNECTION_STRING):
    return sqlite3.connect(dsn)


class BaseRepository:
    def __init__(self, conn=None):
        if conn is None:
            self.db_conn = get_db_conn(dsn)
        else:
            self.db_conn = conn
        self.cursor = self.db_conn.cursor()


class DomainRepository(BaseRepository):
    def _prettify_index(self, data) -> Table:
        table = Table(title="Add domains")
        for header in data["headers"]:
            table.add_column(header)

        for row in data["rows"]:
            rowid, name = data
            table.add_row(str(rowid), str(name))

        return table

    def index(self, pretty=True) -> Union[dict, Table]:
        """
        Return an domain names in the table.

        If pretty is true, return a rich table representation.
        """
        result = self.cursor.execute(
            "SELECT rowid, name FROM %s" % settings.DOMAINS_TABLE_NAME
        )
        headers = ("ID (rowid)", "Name")
        data = {"headers": headers, "rows": result.fetchall()}
        if pretty:
            data = self._prettify_index(data)

        return data
