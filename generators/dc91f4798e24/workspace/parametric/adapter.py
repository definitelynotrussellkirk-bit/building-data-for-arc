"""Native adapter; settings are private episode-level rule choices."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


_HOME = Path(__file__).resolve().parent
_PATH = _HOME / "prototype.py"
_NAME = "_component_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
exec(compile(_PATH.read_bytes(), str(_PATH), "exec"), _PROTOTYPE.__dict__)

_THRESHOLD_PROGRAM = """(rule!
  (let* ((objs (objects g 0))
         (blue-components (filter (lambda (o) (= (obj-color o) 1)) objs))
         (k (length blue-components)))
    (define (count-selected color)
      (length (filter (lambda (o)
                        (and (= (obj-color o) color)
                             (>= (obj-size o) k)))
                      objs)))
    (let* ((n1 (count-selected 1))
           (n2 (count-selected 2))
           (n3 (count-selected 3))
           (ww (max 1 n1 n2 n3)))
      (grid-from-fn 3 ww
        (lambda (r c)
          (let ((cnt (cond [(= r 0) n1] [(= r 1) n2] [else n3]))
                (color (+ r 1)))
            (if (< c cnt) color 0)))))))"""


def program(settings):
    mode = _PROTOTYPE.validate_settings(settings)
    if mode == "all":
        return (_HOME / "canonical.rkt").read_text(encoding="utf-8")
    return _THRESHOLD_PROGRAM


def generate(seed, settings, demos=3, queries=4):
    episode = _PROTOTYPE.generate(seed, settings, demos=demos, queries=queries)
    episode["program_solution"] = program(settings)
    return episode

