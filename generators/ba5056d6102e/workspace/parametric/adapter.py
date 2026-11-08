"""Task-local native adapter, without sibling or global prototype imports."""
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location('native_ba5056d6102e',Path(__file__).with_name('native.py'))
_impl=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_impl)
program=_impl.program
generate=_impl.generate
predict=_impl.predict
inspect=_impl.inspect
public_turn=_impl.public_turn
audit=_impl.audit
