pip install wheel;
Remove-Item -path dist/randomizer -recurse -Confirm:$false;
Set-Location "src/randomizer";
python "setup.py" sdist --dist-dir "../../dist/randomizer/";
python "setup.py" bdist_wheel --dist-dir "../../dist/randomizer/";
Remove-Item -path build -recurse -Confirm:$false;
Remove-Item -path  iog_randomizer.egg-info -recurse -Confirm:$false;
Set-Location "../..";


