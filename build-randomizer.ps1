pip install build;
Remove-Item -path dist/ -recurse -Confirm:$false;
python -m build --sdist --wheel --outdir "dist/";


