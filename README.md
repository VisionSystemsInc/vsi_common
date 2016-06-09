# README #

In order to use these directories, all you have to do is

* Linux (bash)

        #!bash
        source env.bsh

* Windows (batch)

        #!batch
        call env.bat

* Python
    * Prefered

            git clone git@bitbucket.org:visionsystemsinc/vsi_common.git .
            pip install -e .

      This will install an editable version of the library is installed in your python environment. The vsi_common library is the same as the git clone that you can edit and commit.
    * Other options

            pip install .
            python setup.py install
            python setup.py develop
            pip install https://bitbucket.org/visionsystemsinc/vsi_common.git

    * python_util - You still need to import the corresponding `env` script to add python_util to the PYTHONPATH

### What is this repository for? ###

* Common tools we use at VSI for any project/effort where we can use this "VSI" asset

### How do I get set up? ###

* Summary of set up
* Configuration
* Dependencies
* Database configuration
* How to run tests
	* To run all the unit tests for python

			#!bash
			python -m unittest discover -s {vsi_python_dir}

* Deployment instructions

### Contribution guidelines ###

* Adding files
	* Python
		* Add files in the python directory. If it's a new effort, try and add it to the vsi package. If it is a large library and you don't have time to convert everything now, you can add it to the python dir in its own directoy, and add a .pth file for it. Do NOT add .py file in the main python dir
	* Script
		* Linux scripts (written in bash, python, etc..) That are to be CLI only (not a python library meant to be imported EVER) go in the linux directory
			* Start files with

					#!bash
					#!/usr/bin/env bash

						or

					#!/usr/bin/env python

		* Windows scripts (batch mainly) go in the windows directory
			* Start files with

					#!bash
					@echo off

			* If you have a python script you would like to use as a command line, make it a .bat file, and start it with

					1>2# : ^
					'''
					@echo off
					python %~f0 %*
					exit /b
					'''

				* This will start the python in your path, and pass the script and all arguments, as uncorrupted as possible in windows batch. 
				* This can work for anything other than python. 
				* Use pythonw instead for gui tasks.
				* For special characters (like |), you'll need to add an escape character (^|) just to run the command, and then 2^n more for every batch file. So to call this batch file, you'll need 3 carats (^^^|). To escape !, you'll need to create a setlocal ENABLEDELAYEDEXPANSION arond the python call itself (its the %* part that is important). Side effects are currently unknown for using setlocal in this way, so it is not the default yet... 

						#!batch
						setlocal ENABLEDELAYEDEXPANSION
						python %~f0 %*
						endlocal

		* If a script belongs in both (somehow) put it in Windows, and a relative (../Windows/myscript) symlink in Linux

* Writing tests
    * Python
        * Write tests for your modules using the unittest
        * Tests should be stored separately in files names "test_*.py"

				#!python
				import unittest
				class MyTestClass(unittest.TestCase):
				  def test_something(self): #This function MUST start with "test_"
				    doSomething();
				    self.assertEqual('abc', 'a'+'bc')

		* Test classes can contain a setUp function and tearDown function to be called before and after testing starts

				#!python
				class MyTestClass(unittest.TestCase):
				  def setUp(self):
				    self.blah = doSomethingInitialize()
				  def tearDown(self):
				    cleanUpEverything(self.blah)
				    self.blah = None

* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
