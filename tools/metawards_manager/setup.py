import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup \
        (
            name="uq4metawards",  # Replace with your own username
            version="0.0.1",
            author="Christopher Fenton",
            author_email="cjf_uk@hotmail.com",
            description="A set of UQ tools to link to MetaWards",
            long_description=long_description,
            long_description_content_type="text/markdown",
            url="https://github.com/UQ4covid/uq4covid",
            packages=setuptools.find_packages(),
            classifiers=[
                "Programming Language :: Python :: 3",
                "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
                "Operating System :: OS Independent",
            ],
            python_requires='>=3.7',
            entry_points=
            {
                "console_scripts":
                [
                    "uq4metawards-uq3a = uq4metawards.workflow.uq3a:main",
                    "uq4metawards-uq3b = uq4metawards.workflow.uq3b:main",
                    "uq4metawards-uq4 = uq4metawards.workflow.uq4:main"
                ]
            }
        )
