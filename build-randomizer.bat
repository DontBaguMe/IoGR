ECHO OFF
pip install wheel
rd /s /q "dist/randomizer"
cd /d "src/randomizer"
python "setup.py" sdist --dist-dir "../../dist/randomizer/"
python "setup.py" bdist_wheel --dist-dir "../../dist/randomizer/"
rd /s /q "build"
rd /s /q "iog_randomizer.egg-info"
cd /d "../.."


