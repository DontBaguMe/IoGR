pip install bsdiff4 --user
pip install ips.py --user
pip uninstall iog-randomizer -y
call build-randomizer.bat
pip install dist/randomizer/iog_randomizer-4.7.2-py3-none-any.whl --user
python src/gui/gui.py
