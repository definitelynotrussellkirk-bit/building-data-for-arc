"""Native adapter for public 45a5af55 concentric-row folding."""
from pathlib import Path
import hashlib
import importlib.util
import sys

HERE = Path(__file__).resolve().parent
PATH = HERE / 'family.py'
NAME = '_public_45a5af55_' + hashlib.sha256(str(PATH).encode()).hexdigest()
SPEC = importlib.util.spec_from_file_location(NAME, PATH)
G = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = G
SPEC.loader.exec_module(G)

PARAMETERS = G.PARAMETERS
DEFAULT = G.DEFAULT
program = G.program
generate = G.generate
public_turn = G.public_turn
predict = G.predict
analyze = G.analyze
intermediate = G.intermediate
dependency = G.dependency
rival_programs = G.rival_programs
