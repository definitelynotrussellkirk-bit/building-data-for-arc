"""Load this task's exact adjacent module, not a globally cached prototype."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
_spec=spec_from_file_location('native_mirror_1a259ef9a7e7',Path(__file__).with_name('prototype.py'))
_module=module_from_spec(_spec)
_spec.loader.exec_module(_module)
program=_module.program
generate=_module.generate
