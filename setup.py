"""Setup module installation."""

import os

from setuptools import find_packages, setup


def load_requirements(path: str) -> list:
    """Load requirements from the given relative path."""
    with open(path, encoding="utf-8") as file:
        requirements = []
        for line in file.read().split("\n"):
            if line.startswith("-r"):
                dirname = os.path.dirname(path)
                filename = line.split(maxsplit=1)[1]
                requirements.extend(load_requirements(os.path.join(dirname, filename)))
            elif line and not line.startswith("#"):
                requirements.append(line.replace("==", ">="))
        return requirements


if __name__ == "__main__":
    with open("README.md", encoding="utf-8") as readme:
        long_desc = readme.read()

    setup(
        name="deltachat_cursed",
        setup_requires=["setuptools_scm"],
        use_scm_version={
            "root": ".",
            "relative_to": __file__,
            "tag_regex": r"^(?P<prefix>v)?(?P<version>[^\+]+)(?P<suffix>.*)?$",
            "git_describe_command": "git describe --dirty --tags --long --match v*.*.*",
        },
        description="Delta Chat client for the command line",
        long_description=long_desc,
        long_description_content_type="text/markdown",
        author="The Cursed Delta Contributors",
        author_email="adbenitez@nauta.cu",
        url="https://github.com/adbenitez/deltachat-cursed",
        package_dir={"": "src"},
        packages=find_packages("src"),
        keywords="deltachat tui client ncurses",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: End Users/Desktop",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: POSIX",
            "Programming Language :: Python :: 3",
        ],
        entry_points="""
            [console_scripts]
            curseddelta=deltachat_cursed.main:main
            delta=deltachat_cursed.main:main
        """,
        python_requires=">=3.7",
        install_requires=load_requirements("requirements/requirements.txt"),
        extras_require={
            "test": load_requirements("requirements/requirements-test.txt"),
            "dev": load_requirements("requirements/requirements-dev.txt"),
        },
        include_package_data=True,
        zip_safe=False,
    )
