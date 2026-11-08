from __future__ import annotations
import hashlib
import importlib
import inspect
import json
import importlib.util
import sys
from pathlib import Path

TASK = "7f181d3b0012"
repo = Path.cwd()
sys.path.insert(0, str(repo / "shared/runtime"))
source = (repo / "generators" / TASK / "generator.py").resolve()
spec = importlib.util.spec_from_file_location(f"audit_{TASK}_generator", source)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
base = gen.generate(23, 9, difficulty="medium")
unknown_accepted = False
unknown_error = None
try:
    typo = gen.generate(
        23,
        9,
        difficulty="medium",
        __override_contract_unknown_axis__=123,
    )
    unknown_accepted = True
except Exception as exc:  # evidence probe records the actual contract
    typo = None
    unknown_error = f"{type(exc).__name__}: {exc}"

symmetric = [
    [0, 1, 0],
    [1, 0, 1],
    [0, 1, 0],
]
tile_rival = [list(row) for row in symmetric] + [list(row) for row in symmetric]
report = {
    "task_id": TASK,
    "generator_version": gen.VERSION,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "unknown_override_probe": {
        "key": "__override_contract_unknown_axis__",
        "accepted": unknown_accepted,
        "error": unknown_error,
        "same_grid_as_without_typo": typo == base if typo is not None else None,
    },
    "symmetric_domain_probe": {
        "input": symmetric,
        "self_check": gen.self_check(symmetric),
        "observed_axes": gen.observe_overrides(symmetric),
        "plain_vertical_duplication_rival": tile_rival,
        "claim_to_check_against_racket": "for a UD-symmetric legal input, vconcat(g, flip-ud(g)) equals vconcat(g, g)",
    },
    "semantic_contract_present": any(
        hasattr(gen, name)
        for name in ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")
    ),
}
out = Path("../checks/audit/7f181d3b0012/contract-probe.json")
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
