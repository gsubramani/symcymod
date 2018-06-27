Sympy Cython Module Creator
---------------------------

**symcymod** allows easy conversion of multiple sympy expressions
into Cython modules and c code. It makes use of sympy's codegen
utility to create cython files and corresponding code and header
files.

Requirements
------------
**sympy**, **cython**


How to use symcymod?
--------------------

Provide a list of tuples (<name>,<sympy expression>) which corresponds
to pairs of the the name of the function and the corresponding sympy
expression.

**Note:** The order of the parameters in each function might change after
compilation. Passing function arguments as