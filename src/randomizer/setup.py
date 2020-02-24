import os

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name='iog-randomizer',
    version='3.0.3',
    description='The Illusion of Gaia Randomizer',
    author='dontbagume,bryon_w,raeven0',
    packages=setuptools.find_packages(),
    package_data={'': [
        'bin/*.bin',
        'bin/plugins/**/*.bin',
        'bin/plugins/**/**/*.bin'
    ]},
    install_requires=['bitstring'],
    python_requires='>=3.7'
)
