"""Safe dynamic imports for generator-audit scripts.

`dataclasses` and some other module-level features consult ``sys.modules``
while the module body is executing.  ``module_from_spec`` alone does not
register the module, so audit-only loaders must do that explicitly.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


_MISSING = object()


def load_module_from_path(name: str, path: str | Path) -> ModuleType:
    """Execute *path* under *name* with normal import registration semantics."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name, _MISSING)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is _MISSING:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return module
