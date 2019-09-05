pyinstaller ^
    --specpath="./" ^
    --distpath="./dist/gui" ^
    -y ^
    --nowindowed ^
    --noconsole ^
    "src/gui/gui.py" ^
    --name="Illusion of Gaia Randomizer" ^
    && echo D|xcopy /E /Y "./src/randomizer/randomizer/bin" "./dist/gui/Illusion of Gaia Randomizer/randomizer/bin"

