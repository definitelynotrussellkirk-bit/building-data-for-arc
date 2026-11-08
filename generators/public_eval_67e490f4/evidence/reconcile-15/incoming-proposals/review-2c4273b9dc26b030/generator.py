from pathlib import Path
import importlib.util
RULE_TASK_ID='ee_67e490f4'
TASK_ID=GENERATOR_ID='public_eval_67e490f4'
VERSION='1.0.0'
SUMMARY='Crop the large tableau; classify its holes by dihedral shape and fill each with the majority colour among matching external cue objects.'
EXAMPLES_NEEDED=2
HOME=Path(__file__).resolve().parent
PROGRAM=(HOME/'reference.rkt').read_text()
def _e():
 p=HOME/'workspace/parametric/engine.py';s=importlib.util.spec_from_file_location('_e67',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def generate(seed=0,sample_index=0,difficulty=None):
 if difficulty not in (None,'easy','medium','hard'):raise ValueError('difficulty')
 return _e().make(seed,sample_index,difficulty=='hard')
def self_check(g,**_):return _e().self_check(g)
