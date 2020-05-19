rem This will rebuild and install a local copy of metawards_manager

python setup.py sdist bdist_wheel
pip install .