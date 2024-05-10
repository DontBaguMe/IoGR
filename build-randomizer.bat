ECHO OFF
pip install build
rd /s /q "dist"
python -m build --sdist --wheel --outdir "dist/"


