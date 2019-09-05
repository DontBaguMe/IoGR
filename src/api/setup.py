import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='iog-randomizer-api',
    version='0.0.10',
    description='The Illusion of Gaia Randomizer API',
    author='bryon_w',
    packages=setuptools.find_packages(),
    install_requires=['flask', 'flask_expects_json', 'iog_randomizer'],
    python_requires='>=3.7'
)
