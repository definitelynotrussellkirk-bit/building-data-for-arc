from pathlib import Path
import importlib.util
RULE_TASK_ID='ee_8b7bacbf'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
p=Path(__file__).resolve().parent/'workspace/parametric/family.py';s=importlib.util.spec_from_file_location('_g8b',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def generate(seed=0,sample_index=0,difficulty=None,**overrides):
 if overrides or difficulty not in (None,'easy','medium','hard'): raise ValueError('bad controls')
 return m.scene(seed,sample_index)
def self_check(grid,**kwargs): return []
