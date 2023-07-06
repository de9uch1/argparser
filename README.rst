argparser: argument parser for shell script
###########################################

INSTALLATION
============
I recommend to use pipx to install argparser.

.. code:: bash

   pipx install git+https://github.com/de9uch1/argparser.git

Also you can install by pip.

.. code:: bash

   pip install git+https://github.com/de9uch1/argparser.git

USAGE
=====
1. Define add_args() function and add arguments.
2. The first argument of :code:`argparser add` is a variable name in the script which will
   be set to the given argument value.
3. The second positional argument, --long/-l and --short/-s options will be
   command line argument names.
4. Other arguments of :code:`argparser add` can be shown by :code:`argparser add --help`.
5. :code:`eval $(add_args | argparser parse $@)` parses command line arguments.

The parser is based on `argparse.ArgumentParser <https://docs.python.org/3/library/argparse.html>`_ from Python.

EAMPLE
======
.. code:: bash

   #!/bin/bash

   function add_args() {
       argparser setup $0 "Test script."
       argparser add FILE        file
       argparser add WORKERS  -l num-workers  -s n --type int --default 8
       argparser add USER_IDS -l user-ids     -s u --type int --nargs "*"
       argparser add BETA     -l experimental      --action store_true
       argparser add LANGUAGE -l lang              --choices en de ja
   }
   eval $(add_args | argparser parse $@)

   echo $FILE
   echo $WORKERS
   echo ${USER_IDS[@]}
   $BETA && echo T || echo F
   echo $LANGUAGE

If the above script is executed with this following command line,

.. code:: bash

   ./script.sh --file log.txt --num-workers 16 -u 100 200 --experimental --lang ja

The variables in the script will be set to:

- :code:`FILE=log.txt`
- :code:`WORKERS=16`
- :code:`USER_IDS=(100 200)`  # Stored in array
- :code:`BETA=true`           # This is helpful for such situation: :code:`if $BETA; then ...`
- :code:`LANGUAGE=ja`

You can also see the help messages of the defined arguments by :code:`./script.sh --help`.

NOTE
====
This software was inspired by https://github.com/ko1nksm/getoptions .
