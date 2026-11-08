"""Exact-path native adapter for e68b376152cd order-policy family."""
import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_e68_order_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
_IMPL = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_IMPL)

program = _IMPL.program
generate = _IMPL.generate
predict = _IMPL.predict
intermediate = _IMPL.intermediate
pack_intermediate = _IMPL.pack_intermediate
public_view = _IMPL.public_view

# The union keeps the existing helpers available for source-bound old tests.
_UNION_PATH = Path(__file__).resolve().with_name("union.py")
_UNION_SPEC = importlib.util.spec_from_file_location("_union_e68b376152cd", _UNION_PATH)
_UNION = importlib.util.module_from_spec(_UNION_SPEC)
_UNION_SPEC.loader.exec_module(_UNION)
program = _UNION.program
generate = _UNION.generate
