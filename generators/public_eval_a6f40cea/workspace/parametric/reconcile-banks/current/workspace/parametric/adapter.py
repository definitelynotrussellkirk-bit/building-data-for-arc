"""Native adapter for the public a6f40cea occluded-wire family."""
from pathlib import Path
import hashlib
import importlib.util
import sys

BASE = Path(__file__).resolve().parent
PATH = BASE / "family.py"
NAME = "_a6_family_" + hashlib.sha256(str(PATH).encode()).hexdigest()
SPEC = importlib.util.spec_from_file_location(NAME, PATH)
G = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = G
exec(compile(PATH.read_bytes(), str(PATH), "exec"), G.__dict__)

program = G.program
generate = G.generate
present = G.present
