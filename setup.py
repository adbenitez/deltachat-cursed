"""Setup module installation."""

import os
import re

from setuptools import find_packages, setup

if __name__ == "__main__":
    MODULE_NAME = "deltachat_cursed"
    with open(os.path.join("src", MODULE_NAME, "__init__.py")) as fd:
        version = re.search(r"__version__ = \"(.*?)\"", fd.read(), re.M).group(1)

    with open("README.md") as f:
        long_desc = f.read()

    with open("requirements.txt", encoding="utf-8") as file:
        install_requires = [
            line.replace("==", ">=")
            for line in file.read().split("\n")
            if line and not line.startswith(("#", "-"))
        ]
    with open("requirements-test.txt", encoding="utf-8") as req:
        test_deps = [
            line.replace("==", ">=")
            for line in req.read().split("\n")
            if line and not line.startswith(("#", "-"))
        ]

    setup(
        name=MODULE_NAME,
        version=version,
        description="A ncurses Delta Chat client",
        long_description=long_desc,
        long_description_content_type="text/markdown",
        author="The Cursed Delta Contributors",
        author_email="adbenitez@nauta.cu",
        url="https://github.com/adbenitez/deltachat-cursed",
        package_dir={"": "src"},
        packages=find_packages("src"),
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Users",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: POSIX",
            "Programming Language :: Python :: 3",
        ],
        entry_points="""
            [console_scripts]
            curseddelta={}:main
        """.format(
            MODULE_NAME
        ),
        python_requires=">=3.5",
        install_requires=install_requires,
        extras_require={"test": test_deps},
        include_package_data=True,
        zip_safe=False,
    )
