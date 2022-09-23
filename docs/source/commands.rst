Commands Reference
==================

You can find help for any command by append **-h** to every command.

Global flags
------------

:--help, -h: Show help.

:--version: Output version information.

:--debug: For development use only.

dkim
----

keygen
^^^^^^

Used for generating DKIM keys.

Arguments
"""""""""

:domain: The domain name for which this key will belong.

:selector: A unique string used to identify this key later on.
            Will be used in TXT redords.

Selectors are useful when a domain has multiple DKIM keys or when you want to
be able to easily swap out keys later on by allowing you to easily
easily invalidate DNS records.

Flags
"""""

:--quiet, -q: Don't output key contents to screen.

:--save: Save the key to disk and add it to Rspamd's map. Will also reload
            the Rspamd service.

show
^^^^

Display a domain's existing DKIM key.

Arguments
"""""""""

:domain: The domain name in question.

domain
------

Manage your domain names.

add
^^^

Add a domain name.

Arguments
"""""""""

:name: The domain name to add.

Flags
"""""

:--dkim: Generate and save a DKIM key for this domain as well.
:--selector: The selector for the DKIM key. Defaults to current timestamp.
