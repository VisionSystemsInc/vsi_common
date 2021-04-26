# VSI Common

|Linux|Windows|macos|docs|
|--|--|--|--|
|[![CircleCI](https://circleci.com/gh/VisionSystemsInc/vsi_common.svg?style=shield)](https://circleci.com/gh/VisionSystemsInc/vsi_common)|[![Build status](https://ci.appveyor.com/api/projects/status/3a3hd3m41clxd5gw/branch/master?svg=true)](https://ci.appveyor.com/project/andyneff/vsi-common/branch/master)|[![Build Status](https://travis-ci.com/VisionSystemsInc/vsi_common.svg?branch=master)](https://travis-ci.com/VisionSystemsInc/vsi_common)|[![Docs](https://img.shields.io/circleci/build/gh/VisionSystemsInc/vsi_common/master?label=docs)](https://visionsystemsinc.github.io/vsi_common)|

In order to use these directories, all you have to do is

* Linux (bash)

  ```bash
  source env.bsh
  ```

* Windows (batch)

  ```batch
  call env.bat
  ```

* Python

  * Prefered

    ```bash
    pip install git+https://github.com/visionsystemsinc/vsi_common.git
    ```

  * Other options

    ```bash
    git clone git@github.com:visionsystemsinc/vsi_common.git .
    ```

    and one of

      ```bash
      pip install .
      python setup.py install
      ```

    Developers of a module should install an editable version of the library in your python environment by
    cloning the repo and running one of

      ```bash
      python setup.py develop
      pip install -e .
      ```

### What is this repository for? ###

* Common tools we use at VSI for any project/effort where we can use this "VSI" asset

### How do I get set up? ###

* Summary of set up
* Configuration
* Dependencies
* Database configuration
* How to run tests

  * To run all the unit tests for python

    ```bash
    python -m unittest discover -s {vsi_python_dir}
    ```

* Deployment instructions

### Contribution guidelines ###

* Adding files
  * Python

    * Add files in the python directory. If it's a new effort, try and add it to the vsi package. If it is a large library and you don't have time to convert everything now, you can add it to the python dir in its own directory, and add a .pth file for it. Do NOT add .py file in the main python dir

  * Script

    * Linux scripts (written in bash, python, etc..) That are to be CLI only (not a python library meant to be imported EVER) go in the linux directory

      * Start files with

        ```bash
        #!/usr/bin/env bash
        ```

        or

        ```bash
        #!/usr/bin/env python
        ```

    * Windows scripts (batch mainly) go in the windows directory

      * Start files with

        ```batch
        @echo off
        ```

      * If you have a python script you would like to use as a command line, make it a .bat file, and start it with

        ```batch
        1>2# : ^
        '''
        @echo off
        python %~f0 %*
        exit /b
        '''
        ```

        * This will start the python in your path, and pass the script and all arguments, as uncorrupted as possible in windows batch.
        * This can work for anything other than python.
        * Use pythonw instead for gui tasks.
        * For special characters (like |), you'll need to add an escape character (^|) just to run the command, and then 2^n more for every batch file. So to call this batch file, you'll need 3 carats (^^^|). To escape !, you'll need to create a setlocal ENABLEDELAYEDEXPANSION arond the python call itself (its the %* part that is important). Side effects are currently unknown for using setlocal in this way, so it is not the default yet...

          ```batch
          setlocal ENABLEDELAYEDEXPANSION
          python %~f0 %*
          endlocal
          ```

    * If a script belongs in both (somehow) put it in Windows, and a relative (../Windows/myscript) symlink in Linux

* Writing tests

  * Python

    * Write tests for your modules using the unittest
    * Tests should be stored separately in files names "test_*.py"

      ```python
      import unittest
      class MyTestClass(unittest.TestCase):
        def test_something(self): #This function MUST start with "test_"
          doSomething();
          self.assertEqual('abc', 'a'+'bc')
      ```

    * Test classes can contain a setUp function and tearDown function to be called before and after testing starts

      ```python
      class MyTestClass(unittest.TestCase):
        def setUp(self):
          self.blah = doSomethingInitialize()
        def tearDown(self):
          cleanUpEverything(self.blah)
          self.blah = None
      ```

* Code review
* Other guidelines

### Documentation ###

Documentation uses sphinx. To compile documentation, run

```bash
just docs
just docs view
```

Sphinx documentation can be embedded in any source file. There must be a `#*#` comment stating the filename and any `#` comments surrounded with `#**` will be added to sphinx documentation

```bash
# This documentation path will become:
#   {VSI_COMMON_DIR}/docs/example/readme.auto.rst
# Other files will refer to is the document with .auto. in the name
#*# example/readme.rst


# The following three lines are included

#**
# .. note::
#
#     You can not run the script and download in one call, you must call new_just as a file, not a pipe stream. ``
#**

# This line is not documentation
# No #** at the beginning of this line
```

#### Documentation FAQ

1. Why is there an `bash:env` directive, when `envvar` already exists?

    - They are both for documenting environment variables, `bash:env` should be used for locally scoped variables, that only affect that one file, while `envvar` might affect many files.

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
