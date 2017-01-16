#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import codecs
import os
import re

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

long_description = read('README.rst')

setup(
    name="dockercp",
    version=find_version("dockercp", "__init__.py"),
    description="A simple Docker cp implementaion.",
    long_description=long_description,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Utilities",
    ],
    keywords='docker container copy',
    author='Ömer Fadıl Usta',
    author_email='omerusta@gmail.com',
    url='https://github.com/usta/dockercp',
    license='BSD',
    packages=find_packages(exclude=["docs"]),
    scripts=["scripts/docker-cp"],
)
