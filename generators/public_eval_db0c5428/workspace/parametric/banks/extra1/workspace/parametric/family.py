"""Exact-path aliases to the self-contained production generator."""
from pathlib import Path
import hashlib,importlib.util,sys
_PATH=Path(__file__).resolve().parents[2]/'generator.py'
_SPEC=importlib.util.spec_from_file_location('_familydb0_'+hashlib.sha256(str(_PATH).encode()).hexdigest()[:16],_PATH)
_IMPL=importlib.util.module_from_spec(_SPEC);sys.modules[_SPEC.name]=_IMPL;_SPEC.loader.exec_module(_IMPL)
for _name in ('integer','check_grid','parse','render','solve','intermediate','make_scene','self_check_scene','sample'):
    globals()[_name]=getattr(_IMPL,_name)
