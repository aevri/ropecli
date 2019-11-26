Rope CLI
========

[Rope](https://github.com/python-rope/rope) is a Python refactoring library,
with integrations into some IDEs.

In order to make it easy to perform large refactorings without relying on an
IDE, and to make refactorings easily repeatable, here is a CLI for performing
these refactorings using rope.

This can make it easier to correctly rebase refactoring commits on top of new
changes, as well as correctly rebasing changes on top of refactorings.

This is ideal for use in conjunction with an automatic formatter like
[black](https://black.readthedocs.io/en/stable/), to minimize any resulting
formatting fixups.

Installation
------------

```
pip install https://github.com/aevri/ropecli.git
```

Summary
-------

```
Usage: rope [OPTIONS] COMMAND [ARGS]...

  A refactoring tool for Python programs.

  Built on the excellent 'rope' refactoring library, which powers the
  refactoring capabilities of a number of IDEs.

Options:
  --help  Show this message and exit.

Commands:
  froms-to-imports  Change the 'from X import Y' statements in PATH to...
  list              List the global entities in PATH.
  move              Move the global entry SOURCE to the TARGET_FILE.
  organize-imports  Organize the import statements in PATH in an
                    opinionated...
  rename            Rename the global entry OLD_NAME in PATH to NEW_NAME.
```


Examples
--------

Given two files, `vegetables.py:`
```python
from sys import stderr
import argparse


def carrots():
    print("carrots!", file=stderr)


def tomatoes():
    print("tomatoes!")


def all():
    carrots()
    tomatoes()
```

and `fruit.py:`

```python
def cherries():
    print("cherries!")
```

We can apply refactorings like the following.

### Convert 'from' imports to regular imports

```bash
rope froms-to-imports vegetables.py
```

Resulting in this change:

```diff
diff --git a/vegetables.py b/vegetables.py
index 86d22fb..6e2b3c4 100644
--- a/vegetables.py
+++ b/vegetables.py
@@ -1,9 +1,8 @@
-from sys import stderr
-import argparse
+import sys


 def carrots():
-    print("carrots!", file=stderr)
+    print("carrots!", file=sys.stderr)


 def tomatoes():
```

### Move functions and classes

```bash
rope move vegetables.py::tomatoes fruit.py
black *.py
```

Note that we also use `black` here, to fix formatting, resulting in this
change:

```diff
diff --git a/vegetables.py b/vegetables.py
index 86d22fb..ba5a551 100644
--- a/vegetables.py
+++ b/vegetables.py
@@ -1,15 +1,11 @@
 from sys import stderr
-import argparse
+import fruit


 def carrots():
     print("carrots!", file=stderr)


-def tomatoes():
-    print("tomatoes!")
-
-
 def all():
     carrots()
-    tomatoes()
+    fruit.tomatoes()
diff --git a/fruit.py b/fruit.py
index b423336..6416371 100644
--- a/fruit.py
+++ b/fruit.py
@@ -1,2 +1,6 @@
+def tomatoes():
+    print("tomatoes!")
+
+
 def cherries():
     print("cherries!")
```

### Move functions and classes with wildcards

```bash
rope move vegetables.py::* fruit.py --exclude vegetables.py::tomatoes
black *.py
```

Note that we also use `black` here, to fix formatting, resulting in this
change:

```diff
diff --git a/vegetables.py b/vegetables.py
index 86d22fb..4561d71 100644
--- a/vegetables.py
+++ b/vegetables.py
@@ -1,15 +1,2 @@
-from sys import stderr
-import argparse
-
-
-def carrots():
-    print("carrots!", file=stderr)
-
-
 def tomatoes():
     print("tomatoes!")
-
-
-def all():
-    carrots()
-    tomatoes()
diff --git a/fruit.py b/fruit.py
index b423336..383c1bc 100644
--- a/fruit.py
+++ b/fruit.py
@@ -1,2 +1,15 @@
+from sys import stderr
+from vegetables import tomatoes
+
+
+def all():
+    carrots()
+    tomatoes()
+
+
+def carrots():
+    print("carrots!", file=stderr)
+
+
 def cherries():
     print("cherries!")
```
