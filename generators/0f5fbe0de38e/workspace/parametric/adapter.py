"""Native adapter; load this task's adjacent module without global import aliases."""
import importlib.util
from pathlib import Path
_spec = importlib.util.spec_from_file_location('native_0f5fbe0de38e', Path(__file__).with_name('native.py'))
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)
program = _impl.program
generate = _impl.generate
public_turn = _impl.public_turn
inspect = _impl.inspect
audit = _impl.audit
