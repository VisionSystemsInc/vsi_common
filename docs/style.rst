
========================
Contributing Style Guide
========================

Bash
----

* Two spaces per indent

* ``then`` and ``do`` on the same line

  .. code-block:: bash

     for x in $(ls); do
       :
     done

     while check_something; do
       :
     done

We like to use `>&` for file descriptors (numbers), and `&>` for filenames

* Redirecting to open file

  .. code-block:: bash

     echo hi 1>&2 # No extra spaces, as bash doesn't allow that

     echo bye >&2 # No extra spaces

* Closing an open file

  .. code-block:: bash

     exec 3>&-

     exec 3&>- # Wrong style. This is dealing with descriptors

* Redirecting to a file

  .. code-block:: bash

     run_some_command &> /dev/null # Spaces added around &>

     run_some_command >& /dev/null # Wrong style. This is dealing with filenames

* Always quote variables and complex strings

  There are many conditions when you need to use quotes, and very few when you need not to, and many when quotes seem optional. Always using quotes vastly reduces the chance of errors from unexpected (and erroneous) input and simplifies remembering when you need and don't need quotes

  .. code-block:: bash

     bvar=${avar}   # Wrong style. Always add quotes
     bvar="${avar}" # Right
     cvar=foo bar   # Wrong style and syntax. This is a complex string, and requires quotes/
                    # This actually executes a command called bar. Instead, make it clear
     cvar="foo" bar # Right
     cvar="foo bar" # Right
     echo ${avar}   # Wrong style. Whitespace is not replicated the same way without quotes
     echo "${avar}"

     # There are a few reason to not quote a variable. Be sure to add a "# noquotes"
     # comment so code reviewers knows these are intended:

     # One is an empty variable that should not be treated as an empty string
     # DRYRUN/optional_flag could be "echo"/"-stuff" or empty string
     ${DRYRUN} some command # noquotes
     some_command ${optional_flag} foo bar # noquotes
     # The preferred way is to use arrays, if it is not overly cumbersome.
     ${DRYRUN[@]+"${DRYRUN[@]}"} some command
     some_command ${optional_flag[@]+"${optional_flag[@]}"} foo bar
     # Since arrays cannot be exported, this is often not viable.

     # Another reason quotes must not be used, is when splitting up a string into an array
     foo="aa:bb:cc:dd"
     IFS=":"
     # This is actively splitting apart a string, and must not be in quotes
     bar=(${foo}) # noquotes

  Quotes should actually not be used in ``[[]]`` expressions. There are a few corner cases the will be treated literally. ``# noquotes`` is not needed for ``[[]]`` expressions.

  .. code-block:: bash

     if [ "${var}" -gt "0" ] && [[ ${foo} =~ ${pattern} ]]; then
       echo "hi"
     fi

  Simple assignments _may_ skip quotes, ``# noquotes`` is not needed as this is easy enough for a code reviewer to see

  .. code-block:: bash

     local a=1
     b=2
     x=(11 22 33 44 "5 5" "6  6")
     cvar=foo
     dvar=foo\ bar  # Wrong style. This is no longer simple. Use quotes
     dvar="foo bar" # Right

  It is best not to use quotes when inside of ``{}``. The expressions inside of ``{}`` can be thought of as already being implicitly quoted (``"``). Adding quotes (``'`` or ``"``) may seem to work at first, but the behavior of explicitly quoting will change between the different versions of bash.

  .. code-block:: bash

     echo "${foo-"b a  r"}"        # Wrong style
     echo "${foo-b a  r}"          # Right
     echo "${foo/"o"/"O"}"         # Wrong style
     echo "${foo/o/O}"             # Right
     echo "${foo/"  "/two spaces}" # Wrong style
     echo "${foo/  /two spaces}"   # Right

  :var:`bash_behavior_pattern_substitution_slash_escape_with_single_quote` is a special case that still needs special care, due to differences in bash behavior between versions.

* Always use ${var} vs $var

  The reason for this policy is consistency and to clarify that certain features in bash only work in the ``{}``, e.g. variable substitution. It's very easy for someone to mistake ``${foo+set}`` for ``$foo+set`` and not ``${foo}+set``.

  .. code-block:: bash

     echo "$PATH"                   # Wrong style
     echo "${PATH}"                 # Right
     echo "${$}"                    # Right
     echo "${-} ${?} ${*-}"         # * and @ need some extra care, so that
     run command "${_}" ${@+"${@}"} # set -eu doesn't error on empty in bash 3.2

* Shorthand for arithmetic expressions

  .. code-block:: bash

     x=(11 22 33 44)
     y=2
     echo "${x[y]} is perfectly acceptable"
     echo "${x[$y]} is violated the {} policy, even though it is valid bash"
     echo "${x[${y}]} is ok too, but the shorthand looks better"
     echo "$((x[y] - y)) is also perfectly acceptable"
     echo "${x:1:y} is also perfectly acceptable"
     echo "${x:1:y+1} is also perfectly acceptable"

     # Do no add quotes to inner expressions
     echo "${x["y"]} ${x["${y}"]}"

     # Associative arrays are not bash 3.2 compatible, and are not
     # arithmetic expressions in the []
     declare -A z
     y=2
     z[y]="This is index y not 2"
     z[$y]="This is index 2" # Wrong style, violates the {} policy
     z[${y}]="This is index 2"
     z[${y}-1]="This is index '2-1', not 1"
     z[$((y-1))]="This is index 1"

* Prefer ``[ ]`` tests to the ``[[ ]]`` construct, prefer ``=`` to ``==``

  .. code-block:: bash

    [ "${avar}" = "foo bar" ]      # Variables are always quoted in [] tests

    [[ ${avar} == "foo bar" ]]     # Wrong style. Use [] and = for normal equality

    [[ ${avar} = foobar* ]]        # Right. Pattern matching is not possible with []

    [[ ${avar} = "foo bar"* ]]     # Right. If quotes are needed, you can use a variable
    pattern="foo bar*"
    [[ ${avar} = ${pattern} ]]     # Ok. Never quote patterned variables in [[ ]] as
                                   # this disables pattern matching---in which case,
                                   # [] can be used instead
    If you are mixing literal and wild cards, you will use quotes
    avar="foo*bar"
    pattern="foo*b"
    [[ ${avar} = "${pattern}"* ]]  # If you want the pattern to refer to a literal asterisk, you need these quotes.
    [[ foo-bar != ${pattern}* ]]   # This would fail, because the * in the pattern would be a wild card, not an *

    [[ ${avar} =~ foobar.+ ]]      # Right. Regex's are not possible with []

    [[ ${avar} =~ "foo bar".+ ]]   # Right. If quotes are needed, you can use a variable
    pattern='foo bar.+'
    [[ ${avar} =~ "${pattern}" ]]  # Wrong, this disables regex matching
    [[ ${avar} =~ ${pattern} ]]    # Good. Don't quote variables in [[ ]]
    pattern='f\+ bar.+'            # The first + is an escaped literal +
    [[ ${avar} =~ ${pattern} ]]    # Good. Don't quote variables in [[ ]]

    [[ 3 < 4 ]]                    # Wrong style
    [ "3" -lt "4" ]]               # Right

    [[ 3.5 < 4.0 ]]                # Wrong. Floating point comparison not possible with [], [[]] or (())
    if awk '{if (3.5 < 4.0) {exit 0} else {exit 1}}'; then # Floating point is possible with awk

* Checking to see if a variable exists

  .. code-block:: bash

     if [ -z "${variable+set}" ]; then # If not set
       do_something
     fi

     if [ -n "${variable+set}" ]; then # If set
       do_something
     fi

     if [ -z "${variable:+set}" ]; then # If not set OR set to null
       do_something
     fi

     if [ -n "${variable:+set}" ]; then # If set AND not null
       do_something
     fi

* Checking to see if an array exists before accessing it

  .. code-block:: bash

     arr=(${foo+"${foo[@]}"}) # WRONG

  * ``arr`` will be empty if the first element of ``foo`` (``"${foo[0]}"``) doesn't exist. Unless this is desired, instead use

  .. code-block:: bash

     ${foo[@]+"${foo[@]}"}
     ${foo[@]+"${!foo[@]}"}
     ${foo[@]+"${foo[*]}"}

* Scripting file naming and shebangs

  * Files that are only meant to be sourced should have a ``.bsh`` extension, and should have the following header:

    .. code:: bash

       #!/usr/bin/env false bash

       if [[ ${-} != *i* ]]; then
         source_once &> /dev/null && return 0
       fi

    * ``false`` signifies this file is for sourcing only. The ``bash`` at the end of the line tricks most editors into parsing the file as bash.

    * ``source_once`` is a component that will cause the file to only be sourced one time, even if other files attempt to source the file multiple times. This improves load time and debugging as the same files are not loaded multiple times. See :file:`source_once.bsh` for more information

  * Some files need to retain ``sh`` compatibility, and should have a ``.sh`` extension instead

  * Files that should be run as executable, should have 755 permissions and the following shebang:

    .. code:: bash

       #!/usr/bin/env bash

  * Files that can be sourced or executed should follow the same rules as executable scripts in addition to:

    * Most of the code should be contained in functions

    * The main function should have the same name as the file

    * The following footer should be used:

      .. code:: bash

         if [ "${BASH_SOURCE[0]}" = "${0}" ] || [ "$(basename "${BASH_SOURCE[0]}")" = "${0}" ]; then
           the_main_function_name "${@}"
           exit $?
         fi

      * This will only execute ``the_main_function_name`` when the script is being called, not sourced.

  * **Circular imports**: While :bash:func:`source_once.bsh source_once` will prevent some circular source issues, this does not help in interactive mode. :bash:func:`source_once.bsh source_once` is disabled in interactive mode because is someone changes a file, and sources it again, they should expect to get those changes, not have it "sourced only once ever" (it is also disabled for cnf speed reasons). Circular dependencies are handled using the :bash:func:`circular_source.bsh circular_source` function instead.

    .. code:: bash

       source something_normal.bsh
       source "${VSI_COMMON_DIR}/linux/circular_source.bsh"
       circular_source "${VSI_COMMON_DIR}/linux/docker_functions.bsh" || return 0

    * ``|| return 0`` makes it so that the current file is sourced the first time in the infinite loop, and stops the loop the second go around. Otherwise it might actually get sourced a total of two times, which is not detrimental but may have undesired effects (especially for CLI's)

* Coverage: bashcov can be used to create a coverage report. In order to designation a section of code as "no coverage", use ``# :nocov:`` before and after the code you want to not be reported on. There are additional flags for that can be excluded on macos (``:nocov_mac:``), Linux (``:nocov_linux:``), and Windows (``:nocov_nt:``). You can also designate an area to not be covered based on the version of bash: ``:nocov_bash_4.1:`` for no coverage on bash 4.1 and newer, or ``:nocov_lt_bash_4.4`` for no coverage on bash 4.4 and older. Multiple flags may be combined, where ``:nocov_nt: :nocov_bash_4.0:`` means no coverage on windows OR bash 4.0 or newer.

Python
------

* We use pep8, except two spaces per indent
* (Not yet implemented) Coverage: pycoverage is used to create a coverage report. A line or branch of code can be excluded by adding a comment that includes ``pragma: no cover``. An os specific pragma can be added, such as ``pragma: no linux cover`` for only on Windows, or ``pragma: no nt cover`` for only on mac and linux.

J.U.S.T. Plugins
----------------

* Just plugins that use docker-compose should specify the ``docker-compose.yml`` file with every command, to prevent unintended consequences in case the user sets ``COMPOSE_FILE``