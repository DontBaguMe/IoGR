pip install wheel &
cd /d "src/randomizer" &
python "setup.py" sdist --dist-dir "../../dist/randomizer/" &
python "setup.py" bdist_wheel --dist-dir "../../dist/randomizer/" &
REM python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/randomizer/* && ^
rmdir build /s /q &
rmdir iog_randomizer.egg-info /s /q &
cd /d "../.."


