"""Native adapter loading only its own adjacent implementation."""
import importlib.util
from pathlib import Path

_path=Path(__file__).resolve().with_name("prototype.py")
_spec=importlib.util.spec_from_file_location("_af6e765bcc41_frame_prototype",_path)
_impl=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)
program=_impl.program
generate=_impl.generate
validate_grid=_impl.validate_grid
first_stage=_impl.first_stage
mirror=_impl.mirror
analyze=_impl.analyze
