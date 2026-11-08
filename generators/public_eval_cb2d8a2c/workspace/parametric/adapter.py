"""Native interface; all executable resources live beside this file."""
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location('_cb2d8a2c_model',Path(__file__).with_name('model.py'))
_model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_model)
program=_model.program
generate=_model.generate
public_turn=_model.public_turn
solve=_model.solve
inspect=_model.inspect
scene=_model.scene
rival_programs=_model.rival_programs
rival_predict=_model.rival_predict
DEPENDENCY=_model.DEPENDENCY
causal_case=_model.causal_case
