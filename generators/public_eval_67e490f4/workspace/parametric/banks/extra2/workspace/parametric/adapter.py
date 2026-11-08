"""Task-local native adapter for the 67e490f4 shape-vote family."""
from pathlib import Path
import importlib.util

path = Path(__file__).with_name('model.py')
spec = importlib.util.spec_from_file_location('public_eval_67e490f4_model', path)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
program = model.program
generate = model.generate
