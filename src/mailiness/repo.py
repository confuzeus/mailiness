import sqlite3
from typing import Optional, Union

import bcrypt
from rich.table import Table

from mailiness import g


def get_db_conn(dsn=g.config["db"]["connection_string"]):
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
            "SELECT rowid, name FROM %s" % g.config["db"]["domains_table_name"]
        )
        self.data["rows"] = result.fetchall()
        return self._prettify_data() if pretty else self.data

    def create(self, name: str, pretty=True) -> Union[dict, Table]:
        """
        Add a domain name to the database and return the result.

        If pretty is true, return a rich table representation.
        """
        result = self.cursor.execute(
            f"INSERT INTO {g.config['db']['domains_table_name']} VALUES(?) RETURNING rowid, name",
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
                f"UPDATE {g.config['db']['domains_table_name']} SET {what}=? WHERE {what}=? RETURNING rowid, name",
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
            f"DELETE FROM {g.config['db']['domains_table_name']} WHERE name=?", [name]
        )
        self.db_conn.commit()


class UserRepository(BaseRepository):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data["headers"] = ("ID (Row id)", "Email", "Quota (GB)")

    def _set_data(self, rows: list[tuple]):

        data = [list(row) for row in rows]

        for row in data:
            quota = int(row[2])
            row[2] = quota / 1_000_000_000
        self.data["rows"] = data

    def index(self, domain: Optional[str] = None, pretty=True) -> Union[dict, Table]:
        """
        Return a list of all users.

        If domain is provided, filter the list to show this domain's users only.
        """
        stmt = f"SELECT rowid, email, quota FROM {g.config['db']['users_table_name']}"
        if domain:
            result = self.cursor.execute(
                f"SELECT rowid FROM {g.config['db']['domains_table_name']} WHERE name=?",
                [domain],
            )
            row = result.fetchone()
            if len(row) < 0:
                raise Exception(f"Domain {domain} doesn't exist")
            domain_id = int(row[0])
            stmt += f" WHERE domain_id={domain_id}"

        result = self.cursor.execute(stmt)

        self._set_data(result.fetchall())
        return self._prettify_data() if pretty else self.data

    def _hash_password(self, password: str) -> str:
        h = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        s = h.decode("utf-8")

        if g.config.getboolean("users", "insert_password_hash_prefix"):
            s = g.config["users"]["password_hash_prefix"] + s

        return s

    def _get_domain_id_from_email(self, email: str) -> int:
        _, domain = email.split("@")
        result = self.cursor.execute(
            f"SELECT rowid FROM {g.config['db']['domains_table_name']} WHERE name=?",
            [domain],
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
            f"INSERT INTO {g.config['db']['users_table_name']} VALUES (?,?,?,?) RETURNING rowid, email, quota",
            [domain_id, email, hashed_password, quota_bytes],
        )
        self._set_data(result.fetchall())
        self.db_conn.commit()

        return self._prettify_data() if pretty else self.data

    def edit(
        self,
        email: str,
        new_email: Optional[str] = None,
        password: Optional[str] = None,
        quota: Optional[int] = None,
    ):
        stmt = f"UPDATE {g.config['db']['users_table_name']} SET %s WHERE email=?"
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
            f"DELETE FROM {g.config['db']['users_table_name']} WHERE email=?", [email]
        )
        self.db_conn.commit()


class AliasRepository(BaseRepository):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data["headers"] = ("ID (Row id)", "From", "To")

    def _get_domain_id(self, domain: str) -> int:
        result = self.cursor.execute(
            f"SELECT rowid FROM {g.config['db']['domains_table_name']} WHERE name=?",
            [domain],
        )
        row = result.fetchone()
        if len(row) < 1:
            raise Exception(f"Domain {domain} doesn't exist.")

        return int(row[0])

    def _get_domain_id_from_email(self, email: str) -> int:
        _, domain = email.split("@")
        return self._get_domain_id(domain)

    def index(self, domain: Optional[str] = None, pretty=True) -> Union[dict, Table]:
        """
        List all aliases.

        If domain is provided, filter the list to show only this domain's aliases.
        """
        stmt = f"SELECT rowid, from_address, to_address FROM {g.config['db']['aliases_table_name']}"
        if domain:
            domain_id = self._get_domain_id(domain)
            stmt += f" WHERE domain_id={domain_id}"

        result = self.cursor.execute(stmt)
        self.data["rows"] = result.fetchall()

        return self._prettify_data() if pretty else self.data

    def create(
        self, from_address: str, to_address: str, pretty=True
    ) -> Union[dict, Table]:
        """
        Create a new alias pointing from from_address to to_address.
        """
        domain_id = self._get_domain_id_from_email(from_address)
        result = self.cursor.execute(
            f"INSERT INTO {g.config['db']['aliases_table_name']} VALUES (?,?,?) RETURNING rowid, from_address, to_address",
            [domain_id, from_address, to_address],
        )
        self.data["rows"] = result.fetchall()
        self.db_conn.commit()

        return self._prettify_data() if pretty else self.data

    def edit(
        self,
        from_address: str,
        new_from: Optional[str] = None,
        to_address: Optional[str] = None,
        pretty=True,
    ) -> Union[dict, Table]:
        stmt = f"UPDATE {g.config['db']['aliases_table_name']} SET %s WHERE from_address=? RETURNING rowid, from_address, to_address"
        placeholders = []
        bindings = []
        if new_from:
            _, old_domain = from_address.split('@')
            _, new_domain = from_address.split('@')
            if old_domain != new_domain:
                domain_id = self._get_domain_id_from_email(new_from)
                placeholders.append("domain_id=?")
                bindings.append(domain_id)
            placeholders.append("from_address=?")
            bindings.append(new_from)

        if to_address:
            placeholders.append("to_address=?")
            bindings.append(to_address)

        stmt = stmt % ",".join([str(i) for i in placeholders])
        bindings.append(from_address)
        result = self.cursor.execute(stmt, bindings)
        self.data["rows"] = result.fetchall()
        self.db_conn.commit()

        return self._prettify_data() if pretty else self.data

    def delete(self, from_address: str):
        self.cursor.execute(
            f"DELETE FROM {g.config['db']['aliases_table_name']} WHERE from_address=?",
            [from_address],
        )
        self.db_conn.commit()
