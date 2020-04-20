# -*- coding: utf-8 -*-
import re
import os

from setuptools import setup, find_packages


MODULE_NAME = 'cursed_delta'
with open(os.path.join(MODULE_NAME, '__init__.py')) as fd:
    version = re.search(
        r'__version__ = \'(.*?)\'', fd.read(), re.M).group(1)

with open('README.md') as f:
    long_desc = f.read()


setup(
    name=MODULE_NAME,
    version=version,
    description='A curse Delta Chat client',
    long_description=long_desc,
    author='The Cursed Delta Contributors',
    author_email='adbenitez@nauta.cu',
    url='https://github.com/adbenitez/cursed_delta',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Users',
                 'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                 'Operating System :: POSIX',
                 'Programming Language :: Python :: 3'],
    entry_points='''
        [console_scripts]
        curseddelta={}:main
    '''.format(MODULE_NAME),
    python_requires='>=3.5',
    install_requires=['deltachat', 'urwid'],
    include_package_data=True,
    zip_safe=False,
)
