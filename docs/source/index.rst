.. Mailiness documentation master file, created by
   sphinx-quickstart on Sat Sep 17 15:45:46 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Mailiness
=====================================

**Mailiness** provides you with a CLI to easily manage your mail server.

Installation
------------

Install the app using *pip*:

.. code-block:: console

   pip install mailiness

Now type ``mailiness -h`` to get an overview of the commands available.

To get help on a specific command, simply type ``mailiness command -h``.
For example:

.. code-block:: console

   mailiness dkim -h

The CLI is organized by commands and subcommands. For example, to generate a DKIM key, you
use the *keygen* subcommand available via the *dkim* command as follows:

.. code-block:: console

   mailiness dkim keygen example.com

To view help for subcommands, simply add *-h* at the end.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   server-assumptions
   commands



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
