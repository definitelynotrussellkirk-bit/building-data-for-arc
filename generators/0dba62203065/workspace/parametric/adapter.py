"""Native promotion adapter for the post-lookup repeat-policy family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_SOURCE = Path(__file__).resolve().with_name("prototype.py")
if _SOURCE.is_symlink() or not _SOURCE.is_file():
    raise ImportError("adapter requires adjacent regular prototype.py")
_BODY = _SOURCE.read_bytes()
_NAME = "_0dba_repeat_policy_" + hashlib.sha256(str(_SOURCE).encode() + _BODY).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
exec(compile(_BODY, str(_SOURCE), "exec"), _PROTOTYPE.__dict__)


def _policy(settings):
    if type(settings) is not dict or set(settings) != {"repeat_policy"}:
        raise ValueError("settings must contain exactly repeat_policy")
    return _PROTOTYPE.validate_policy(settings["repeat_policy"])


def program(settings):
    return _PROTOTYPE.program_for(_policy(settings))


def generate(seed, settings, demos, queries):
    policy = _policy(settings)
    _PROTOTYPE.validate_request(seed, demos, queries)
    return _PROTOTYPE.generate_episode(seed, policy, demos, queries)
