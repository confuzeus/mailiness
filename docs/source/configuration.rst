Configuration
=============

We look for a configuration file at ``/etc/mailiness.ini`` by default.

You can influence this by setting the ``CONFIG_FILE`` environment variable.

If no config is found, a default one will be created with the following
contents:

.. code-block:: ini

   [mail]
   vmail_directory = /var/vmail

   [db]
   connection_string = /var/local/mailserver.db
   domains_table_name = domains
   users_table_name = users
   aliases_table_name = aliases

   [users]
   insert_password_hash_prefix = True
   password_hash_prefix = {BLF-CRYPT}

   [spam]
   dkim_private_key_directory = /var/lib/rspamd/dkim
   dkim_maps_path = /etc/rspamd/dkim_selectors.map

You can view the config file using the ``config show`` command.

Configuration file
------------------

The config file is organized in sections. We currently have the following:

* mail - For emails.
* db - For database configuration.
* users - For virtual users.
* spam - For spam related functionality.

mail
^^^^

**vmail_directory** Where the virtual mail directory is located.

db
^^

**connection_string** The full path to the sqlite database.

**domains_table_name** The name of the table containing domain names.

**users_table_name** The name of the table containing virtual users.

**aliases_table_name** The name of the table containing virtual aliases.

users
^^^^^

**insert_password_hash_prefix** Whether to prepend the hash algorithm to the password hash.
This depends on how you configured Dovecot to parse password hashes.

**password_hash_prefix** The hash algorithm's prefix. We currently support
BLF-CRYPT only.

spam
^^^^

**dkim_private_key_directory** Full path to where DKIM private keys are stored.

**dkim_maps_path** Full path to the Rspamd selectors maps file.
