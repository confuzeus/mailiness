Development
===========

Set the environment variable ``CONFIG_FILE`` to something like ``/tmp/mailiness.ini``
before running tests. The app will automatically create an appropriate config
file then.

You can also provide your own config file but all of the dangerous updates
and database stuff has been mocked in tests anyway so no need to go that far.

Format the code with *black* and *isort* then lint everything with *flake8*
before committing.
