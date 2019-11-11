.. default-domain:: bash

===================================
J.U.S.T. Quickstart Guide for Users
===================================

This is a quickstart guide for the intended customers of a just project. This guides will teach you how to:

* Use a just project
* Identify some common issues and how to collect relevant information to pass on to the developers to help you solve your problems

----------------
What is J.U.S.T.
----------------

Think of :file:`just` as a bunch of scripts all wrapped into one command (or script), with the added benefit that it works on Linux, Windows (provided ``git`` is installed), and macos without additional dependencies.

The developer will create a number of tasks, and assign them to just targets. For example, if there was a ``compile`` target that compiles the code, you run ``just compile`` to run that target.

A typical setup is:

* To update everything with new code you checked out: ``just sync``
* To compile the code: ``just compile``
* To run the code: ``just run``

All of these target names can be customized by the developer, but ``just sync`` is a very common one to remember. The point of this is to "do all the things you usually forget when you just checked out a new version of the code", like compiling code or updating a database, etc...

You can always run :cmd:`just help` will list all the commands available in your project, with a short description for each command.

---------------
Getting started
---------------

You start out by downloading your software, this is usually done by ``git clone``. It's important that the ``--recursive`` be included, or else submodules will be missing and you'll need to initialize them with some more git commands. So start with ``git clone --recursive {git repo url here}``, and ``cd`` into the project directory.

Every time you open a new terminal window on your computer, you will need to start ``bash``, change directory (``cd``) into the project directory and run ``source setup.env`` (``. setup.env`` is a shortened version of the same command) from your project folder. This will setup :file:`just` (add just to your ``PATH``) so that you can run :file:`just` by typing ``just``, instead of ``./external/vsi_common/linux/just``, which is a bit wordy and inconvenient.

Start off by running :cmd:`just help`, to see the list of all advertised just commands. There are a few commands that are in every just project:

* ``-h``/``--help``/``help`` - Print out the help
* ``--dryrun``/``-n`` - Dry run mode. Some commands can be run in dry run mode, which means they are printed out instead of run. This can be useful for debugging purposes. You have to add this flag *before* the target name, not after
* ``--version`` - Print out the version of :file:`just` you currently using
* ``--wrap`` - Commands in :file:`just` run in their own environment with dozens of environment variables exported, making it extremely complicated to run some commands outside of :file:`just`. ``just --wrap`` allows you to run any arbitrary command in the just environment, (it wraps the command in just). For example, if you need to start a database that uses environment variables to start correctly, you can run ``just --wrap /opt/db/database_program --db /data/foo.dat``
* ``--run`` - ``--run`` is similar to ``--wrap``, but runs much deeper in the mechanics of :file:`just` in a place called :func:`Justfile caseify`. This is more for debugging, and users are unlikely to use this, unless instructed to do so.
* ``--separator`` - When you are chaining multiple commands together, you can use ``--`` (the default :envvar:`JUST_SEPARATOR`) to separate multiple commands. However if you need to use ``--`` for your own commands, ``--separator`` lets you tell just to use something else for it's separator, (e.g. ``--separator @@``)
* ``--new`` - For developer to create a :file:`new_just` project
* ``--tab`` - For future feature
* ``--latest`` - For future feature

Commands and subcommands
------------------------

You may notice the help is split into two sections, "commands" and "subcommands". A command may or may not take arguments (like a file name), depending on how the developer writes that target. But sometimes we group together multiple word commands, and we call those special arguments "subcommands".

.. code-block:: text

   Subcommands
   -----------
   test
       int               Run integration tests

``int`` is a subcommand of ``test``, and can be run by saying ``just test int``

Command chaining
----------------

Multiple commands can be run in one just command. Imagine the following :cmd:`just help` output:

.. code-block:: text

   List of possible just commands:
   -----------------------------------
   compile   Compiles project, takes no arguments
   print     Echos out all the remaining arguments
   process   Processes the first argument

   Subcommands
   -----------
   build
       docker        Builds docker images
       singularity   Builds singularity images

You can combine ``compile`` and ``process`` in one just call: ``just compile process data.json``

You can also combine subcommands without having to repeat the command name. In other words: ``just build docker build singularity`` can be shorten to ``just build docker singularity``

Targets like ``print`` will consume all the arguments, but you can break it with a :envvar:`JUST_SEPARATOR` (``--`` by default): ``just compile print Compile is done -- process data.json``


``local.env``
-------------
When you clone a project, all the default settings are loaded into the just project. In order to customize the install for your computer, you can edit a :file:`local.env` (that is auto generated the first time you run :file:`just`). You are encouraged to customize every setting you need in your :file:``local.env``, however this file will never be committed to the repository, and is only for your local install. For example, if you wanted to change a variable called ``PROJECTX_DATABASE_DIR``, you would add that to your :file:`local.env`:

.. code-block:: bash
   :caption: local.env

   PROJECTX_DATABASE_DIR=/data3/x/run1

You can do anything you want in bash in that file, but is encouraged to:

* Not do anything that takes a long time to run. A second time delay means you have to wait a second every time you run :file:`just`
* Don't print out anything to the screen (except for debugging), it will just clutter the screen

---------------
Troubleshooting
---------------

* I cloned the repo, and when I source :file:`setup.env`, all I see is:

    .. code-block:: bash

      $ . setup.env
      bash: ./external/vsi_common/env.bsh: No such file or directory

    * This probably means you did not successfully clone the submodules of the repository. Check that you have the vsi_common submodule, and try again after fixing

* I ran a command, and saw a lot of output ending with a weird stack trace:

    .. code-block:: bash

      $ just do something

      Call stack
      ----------
      833 defaultify  /opt/projects/just_a_project/external/vsi_common/linux/just_functions.bsh
      102 caseify     Justfile
      1034 _justify   /opt/projects/just_a_project/external/vsi_common/linux/just_functions.bsh
      980 justify     /opt/projects/just_a_project/external/vsi_common/linux/just_functions.bsh
      264 main        /opt/projects/just_a_project/external/vsi_common/linux/just

      /opt/projects/just_a_project/external/vsi_common/linux/just_functions.bsh: line 833: Returned 1

    * This is a just stack trace, and can be very useful to a developer when reporting an error. There may even be multiple stacks for one error, be sure to copy them all

* What do you mean you don't understand?

    .. code-block::

       $ just foo bar
       I don't understand: foo

    * When :file:`just` can't find a target, this is the generic error message you get. Either ``bar`` is not a subcommand of ``foo``, or ``foo`` isn't a command at all.

* ``1: unbound variable`` A number is unbound, what?

    .. code-block:: bash

       $ just docker clean
       /opt/projects/just_a_project/external/vsi_common/linux/just_docker_functions.bsh: line 119: 1: unbound variable

    * Arguments are assigned numbers as the variable names. This means it was expecting an argument, and didn't get one. Typically ``1`` means the first argument, ``2`` means the second argument. However, bash can shift arguments around and a number could be any argument after that number. Either way, it was expecting an argument, and didn't get one. If this was not clear by the help text, please let your developer know this so they can correct that.

* ``unbound variable``

    .. code-block:: bash

       $ just error
       Justfile: line 125: PROJECTX_DATABASE_DIR: unbound variable

    * The variable ``PROJECTX_DATABASE_DIR`` was not set and had no default value. Either the README should have told you to set a value in your :file:`local.env`, or the developer made a mistake and needs to be notified so they can fix it. If you know what the value should be, you are free to just update :file:`local.env`. But if this is erroneous behavior, then it should be reported.