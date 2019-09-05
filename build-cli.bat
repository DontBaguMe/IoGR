pyinstaller ^
    --specpath="./" ^
    --distpath="./dist/cli" ^
    -y ^
    "src/cli/__main__.py" ^
    --name="Illusion of Gaia Randomizer" ^
    && echo D|xcopy /E "./src/randomizer/randomizer/bin" "./dist/cli/Illusion of Gaia Randomizer/randomizer/bin"