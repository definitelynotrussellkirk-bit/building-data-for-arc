"""Task-local native adapter for the 4c7dc4dd transfer-panel family."""
from pathlib import Path
import importlib.util

path = Path(__file__).with_name('model.py')
spec = importlib.util.spec_from_file_location('public_eval_4c7dc4dd_model', path)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
program = model.program
generate = model.generate
