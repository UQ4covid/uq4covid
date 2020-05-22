@echo off

rem This will rebuild and install a local copy of metawards_manager

python -m pip install --upgrade pip
python -m pip install --user --upgrade setuptools wheel
python setup.py sdist bdist_wheel
pip install .