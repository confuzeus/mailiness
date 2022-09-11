import bcrypt
from typing import Optional
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

    def _prettify_data(self) -> Table:
        table = Table(title="Domains")
        for header in self.data["headers"]:
            table.add_column(header)

        for row in self.data["rows"]:
            table.add_row(*[str(col) for col in row])

        return table


class DomainRepository(BaseRepository):
    def index(self, pretty=True) -> Union[dict, Table]:
        """
        Return an domain names in the table.

        If pretty is true, return a rich table representation.
        """
        result = self.cursor.execute(
            "SELECT rowid, name FROM %s" % settings.DOMAINS_TABLE_NAME
        )
        self.data["rows"] = result.fetchall()
        return self._prettify_data() if pretty else self.data

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
        return self._prettify_data() if pretty else self.data

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
        return self._prettify_data() if pretty else self.data

    def delete(self, name):
        """
        Delete a domain name.
        """
        self.cursor.execute(
            f"DELETE FROM {settings.DOMAINS_TABLE_NAME} WHERE name=?", [name]
        )
        self.db_conn.commit()


class UserRepository(BaseRepository):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data["headers"] = ("ID (Row id)", "Email", "Quota")

    def index(self, domain: Optional[str] = None, pretty=True) -> Union[dict, Table]:
        """
        Return a list of all users.

        If domain is provided, filter the list to show this domain's users only.
        """
        stmt = f"SELECT rowid, email, quota FROM {settings.USERS_TABLE_NAME}"
        if domain:
            result = self.cursor.execute(
                f"SELECT rowid FROM {settings.DOMAINS_TABLE_NAME} WHERE name=?",
                [domain],
            )
            row = result.fetchone()
            if len(row) < 0:
                raise Exception(f"Domain {domain} doesn't exist")
            domain_id = int(row[0])
            stmt += f" WHERE domain_id={domain_id}"

        result = self.cursor.execute(stmt)

        self.data["rows"] = result.fetchall()
        return self._prettify_data() if pretty else self.data

    def _hash_password(self, password: str) -> str:
        h = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        s = h.decode("utf-8")

        if settings.INSERT_PASSWORD_HASH_PREFIX:
            s = settings.PASSWORD_HASH_PREFIX + s

        return s

    def _get_domain_id_from_email(self, email: str) -> int:
        _, domain = email.split("@")
        result = self.cursor.execute(
            f"SELECT rowid FROM {settings.DOMAINS_TABLE_NAME} WHERE name=?", [domain]
        )
        row = result.fetchone()
        if len(row) < 1:
            raise Exception(f"Domain {domain} doesn't exist.")

        return int(row[0])

    def _quota_gb_to_bytes(self, quota: int) -> int:
        """
        Dovecot requires quota in bytes.

        Normalize it here.
        """
        return quota * 1_000_000_000

    def create(
        self, email: str, password: str, quota: int, pretty=True
    ) -> Union[dict, Table]:
        """
        Create a new user using the parameters.

        Password will be hashed before being being stored.
        """
        hashed_password = self._hash_password(password)
        domain_id = self._get_domain_id_from_email(email)
        quota_bytes = self._quota_gb_to_bytes(quota)
        result = self.cursor.execute(
            f"INSERT INTO {settings.USERS_TABLE_NAME} VALUES (?,?,?,?) RETURNING rowid, email, quota",
            [domain_id, email, hashed_password, quota_bytes],
        )
        self.data["rows"] = result.fetchall()
        self.db_conn.commit()

        return self._prettify_data() if pretty else self.data

    def edit(
        self,
        email: str,
        new_email: Optional[str] = None,
        password: Optional[str] = None,
        quota: Optional[int] = None,
    ):
        stmt = f"UPDATE {settings.USERS_TABLE_NAME} SET %s WHERE email=?"
        placeholders = []
        bindings = []
        if new_email:
            domain_id = self._get_domain_id_from_email(new_email)
            placeholders.append("domain_id=?")
            placeholders.append("email=?")
            bindings += [domain_id, new_email]
        if password:
            hashed_password = self._hash_password(password)
            placeholders.append("password=?")
            bindings.append(hashed_password)
        if quota:
            quota_bytes = self._quota_gb_to_bytes(quota)
            placeholders.append("quota=?")
            bindings.append(quota_bytes)

        stmt = stmt % ",".join(placeholders)

        bindings.append(email)

        self.cursor.execute(stmt, *[bindings])
        self.db_conn.commit()

    def delete(self, email: str):
        self.cursor.execute(
            f"DELETE FROM {settings.USERS_TABLE_NAME} WHERE email=?", [email]
        )
        self.db_conn.commit()
