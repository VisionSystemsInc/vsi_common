# README #

In order to use these directories, all you have to do is

* Linux (bash)

```
#!bash

source env.bsh

```
* Windows (batch)

```
#!batch

env.bat
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
```
#!bash
            python -m unittest discover -s {vsi_python_dir}
```

* Deployment instructions

### Contribution guidelines ###

* Writing tests
    * Python
        * Write tests for your modules using the unittest
        * Tests should be stored separately in files names "test_*.py"
```
#!python
            import unittest
            class MyTestClass(unittest.TestCase):
              def test_something(self): #This function MUST start with "test_"
                doSomething();
                self.assertEqual('abc', 'a'+'bc')
```
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact