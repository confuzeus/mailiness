Server Assumptions
==================

Mailiness currently requires your server to be setup in a certain way.


Components
----------

Your server should be setup to use Postfix, Dovecot, and Rspamd.

Postfix and Dovecot should fetch virtual mail domains, users, and aliases from a SQLite database.

DKIM
^^^^

Our DKIM functionality is tightly integrated with `rspamd <https://www.rspamd.com/>`_.

When you save a key, three things will happen:

1. An entry will be added to Rspamd's dkim maps file located at */etc/rspamd/dkim_selectors.map*.
2. The private key will be saved at */var/lib/rspamd/dkim/{domain}.{selector}.key*.
3. The rspamd service will be restarted using *systemd*.

Database and schema
^^^^^^^^^^^^^^^^^^^

We currently support SQLite.

We will look for this database at */var/local/mailserver.db* by default.

Schema
++++++

The database will need 3 tables:

1. domains
2. users
3. aliases

Make sure your tables contains the exact columns specified below.

domains table
"""""""""""""

This table contains your virtual domain names.

Here's a SQL query you can use to create it:

.. code-block:: sql

  CREATE TABLE IF NOT EXISTS domains(
    name TEXT NOT NULL UNIQUE
  );

users table
""""""""""""

This will hold virtual users.

Users will have their passwords stored hashed using bcrypt.

They also have a quota. This value is the number of bytes the user is allowed
to use for email storage.

Create this table as follows:

.. code-block:: sql

  CREATE TABLE IF NOT EXISTS users(
    domain_id INTEGER NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT,
    quota INTEGER NOT NULL,
    FOREIGN KEY(domain_id) REFERENCES domains(rowid) ON DELETE CASCADE
  );

aliases table
""""""""""""""

This table stores aliases.

The SQL query:

.. code-block:: sql

  CREATE TABLE IF NOT EXISTS aliases(
    domain_id INTEGER NOT NULL,
    from_address TEXT NOT NULL UNIQUE,
    to_address TEXT NOT NULL,
    FOREIGN KEY(domain_id) REFERENCES domain(rowid) ON DELETE CASCADE
  )
