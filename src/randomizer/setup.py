import os

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name='iog-randomizer',
    version='4.7.2',
    description='The Illusion of Gaia Randomizer',
    author='dontbagume,bryon_w,raeven0',
    packages=setuptools.find_packages(),
    package_data={'': [
        '*.bin',
        '*.asr',
        '*.txt',
        'asar-x86.dll',
        'asar-x64.dll',
        'asar-x64.so'
    ]},
    install_requires=['ips.py', 'bsdiff4'],
    python_requires='>=3.7'
)
