import os

ROM_PATH = os.environ.get("ROM_PATH")
if not ROM_PATH:
    raise ValueError("No ROM_PATH set for IOGR API")