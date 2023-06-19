pip uninstall iog-randomizer -y
call build-randomizer.bat
pip install dist/randomizer/iog_randomizer-4.7.0-py3-none-any.whl --user
python src/gui/gui.py
