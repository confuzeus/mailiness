DKIM_PRIVATE_KEY_DIRECTORY= "/var/lib/rspamd/dkim"

DKIM_MAPS_PATH = "/etc/rspamd/dkim_selectors.map"

# According to https://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html
RSA_PUBLIC_EXPONENT = 65537

# Use 2048 for maximum compatibility as at year 2022.
DKIM_KEY_SIZE = 2048
