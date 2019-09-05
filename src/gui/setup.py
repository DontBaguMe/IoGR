import os

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name='iog-randomizer-gui',
    version='0.0.1',
    description='The Illusion of Gaia Randomizer GUI',
    author='dontbagume,bryon_w',
    packages=setuptools.find_packages(),
    install_requires=['iog_randomizer'],
    python_requires='>=3.7'
)
