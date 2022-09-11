VMAIL_DIRECTORY = "/var/vmail"

DB_CONNECTION_STRING = "/var/local/mailserver.db"

DOMAINS_TABLE_NAME = "domains"

USERS_TABLE_NAME = "users"

DKIM_PRIVATE_KEY_DIRECTORY = "/var/lib/rspamd/dkim"

DKIM_MAPS_PATH = "/etc/rspamd/dkim_selectors.map"

# According to https://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html
RSA_PUBLIC_EXPONENT = 65537

# Use 2048 for maximum compatibility as at year 2022.
DKIM_KEY_SIZE = 2048
