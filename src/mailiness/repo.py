import sqlite3
from typing import Union

from rich.table import Table

from . import settings


def get_db_conn(dsn=settings.DB_CONNECTION_STRING):
    return sqlite3.connect(dsn)


class BaseRepository:
    def __init__(self, conn=None):
        if conn is None:
            self.db_conn = get_db_conn()
        else:
            self.db_conn = conn
        self.cursor = self.db_conn.cursor()
        self.data = {"headers": ("ID (rowid)", "Name"), "rows": []}


class DomainRepository(BaseRepository):
    def _prettify_data(self, data) -> Table:
        table = Table(title="Domains")
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
        self.data["rows"] = result.fetchall()
        return self._prettify_data(self.data) if pretty else self.data

    def create(self, name: str, pretty=True) -> Union[dict, Table]:
        """
        Add a domain name to the database and return the result.

        If pretty is true, return a rich table representation.
        """
        result = self.cursor.execute(
            f"INSERT INTO {settings.DOMAINS_TABLE_NAME} VALUES(?) RETURNING rowid, name",
            [name],
        )
        self.data["rows"] = result.fetchall()
        self.db_conn.commit()
        return self._prettify_data(self.data) if pretty else self.data

    def edit(self, what: str, old: str, new: str, pretty=True) -> Union[dict, Table]:
        """
        Change a domain's "what" attribute from old to new.
        """
        if what in ("name",):
            result = self.cursor.execute(
                f"UPDATE {settings.DOMAINS_TABLE_NAME} SET {what}=? WHERE {what}=? RETURNING rowid, name",
                [new, old],
            )
        else:
            raise ValueError(f"I don't know what {what} is.")
        self.data["rows"] = result.fetchall()
        self.db_conn.commit()
        return self._prettify_data(self.data) if pretty else self.data
