TODO: Convert me to MD format

make_design: A basic design of experiments tool

Originally, this was done without dependencies, but I added the pyDOE2 module in as it currently has a wider user base than us and therefore is more likely to be maintained in a suitable manner. Documentation can be found at: https://pythonhosted.org/pyDOE/, the "2" in the Python module points to this repo https://github.com/clicumu/pyDOE2 which addresses the lack of maintenance and updates in the original pyDOE project. 

This can be called from the command line or used within a Python script without modifications.

To all from the command line run:

"make_design.py <input file> <output file>"

To call from within Python the following code can be used:

<pre>
import make_design

design, header = make_design
</pre>

run_analyses: A simple automated way of calling MetaWards from the design stage through to output