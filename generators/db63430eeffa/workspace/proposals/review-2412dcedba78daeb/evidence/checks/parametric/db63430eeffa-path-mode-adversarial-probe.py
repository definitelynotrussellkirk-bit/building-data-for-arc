from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

from reviewer_support import public_challenge_id

ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE = ROOT / "repo/generators/db63430eeffa/workspace/parametric/prototype.py"
EVIDENCE = ROOT / "checks/parametric/db63430eeffa-path-mode-v1"
OUT = ROOT / "checks/parametric/db63430eeffa-path-mode-adversarial.json"

spec = spec_from_file_location("db63430eeffa_path_mode_adversarial", PROTOTYPE)
assert spec and spec.loader
proto = module_from_spec(spec)
sys.modules[spec.name] = proto
spec.loader.exec_module(proto)

failures = []
checked_inputs = 0
for seed in range(256):
    grids = proto.sample_inputs(seed)
    if len(grids) != proto.PAIR_COUNT:
        failures.append({"seed": seed, "issue": "wrong input count"})
        continue
    for profile, grid in zip(proto.PROFILE_SPECS, grids, strict=True):
        height, width, expected_row_gap, expected_col_gap = profile
        endpoints = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 8
        ]
        observed = (
            len(grid),
            len(grid[0]),
            abs(endpoints[1][0] - endpoints[0][0]),
            abs(endpoints[1][1] - endpoints[0][1]),
        )
        if observed != profile:
            failures.append({
                "seed": seed,
                "issue": "profile drift",
                "expected": profile,
                "observed": observed,
            })
        outputs = [proto.python_mirror(grid, mode) for mode in proto.ALLOWED_PATH_MODES]
        if len({json.dumps(output, separators=(",", ":")) for output in outputs}) != 3:
            failures.append({"seed": seed, "issue": "mode collision", "profile": profile})
        checked_inputs += 1

invalid_seed_cases = [None, True, False, 1.0, 1.75, "1", [], {}]
for value in invalid_seed_cases:
    for name, call in (
        ("path_mode_for_seed", lambda: proto.path_mode_for_seed(value)),
        ("sample_inputs", lambda: proto.sample_inputs(value)),
        ("select_seeds", lambda: proto.select_seeds(value)),
    ):
        try:
            call()
        except TypeError:
            pass
        except Exception as exc:
            failures.append({"issue": "wrong invalid-seed exception", "entry": name, "value": repr(value), "error": type(exc).__name__})
        else:
            failures.append({"issue": "invalid seed accepted", "entry": name, "value": repr(value)})

invalid_modes = [None, True, False, 0, 1.0, "", "both ", "diagonal", [], {}]
valid_grid = proto.sample_inputs(0)[0]
for value in invalid_modes:
    for name, call in (
        ("rule_source", lambda: proto.rule_source(value)),
        ("python_mirror", lambda: proto.python_mirror(valid_grid, value)),
    ):
        try:
            call()
        except ValueError:
            pass
        except Exception as exc:
            failures.append({"issue": "wrong invalid-mode exception", "entry": name, "value": repr(value), "error": type(exc).__name__})
        else:
            failures.append({"issue": "invalid mode accepted", "entry": name, "value": repr(value)})

bad_grid = [row[:] for row in valid_grid]
bad_grid[0][0] = True
try:
    proto.python_mirror(bad_grid, "both")
except ValueError:
    pass
else:
    failures.append({"issue": "boolean ARC cell accepted"})

public_files = sorted((EVIDENCE / "public").glob("*.json"))
private_tokens = (
    "path_mode",
    "diagonal_first",
    "straight_first",
    "rule!",
    "seed",
    "parameters",
)
for path in public_files:
    challenge = json.loads(path.read_text(encoding="utf-8"))
    if path.stem != public_challenge_id(challenge):
        failures.append({"issue": "public filename/content mismatch", "path": str(path)})
    if len(challenge.get("train", [])) != 3 or len(challenge.get("test", [])) != 4:
        failures.append({"issue": "public count mismatch", "path": str(path)})
    if any(set(pair) != {"input"} for pair in challenge.get("test", [])):
        failures.append({"issue": "query label leak", "path": str(path)})
    body = path.read_text(encoding="utf-8")
    leaked = [token for token in private_tokens if token in body]
    if leaked:
        failures.append({"issue": "private token leak", "path": str(path), "tokens": leaked})

report = {
    "schema": "db63430eeffa-path-mode-adversarial-v1",
    "status": "pass" if not failures else "fail",
    "sampler_seeds": 256,
    "sampler_inputs_checked": checked_inputs,
    "invalid_seed_cases_per_entry": len(invalid_seed_cases),
    "invalid_mode_cases_per_entry": len(invalid_modes),
    "public_files_checked": len(public_files),
    "surfaces": [
        "sampler boundary profiles and cross-mode separation",
        "literal numeric/type rejection",
        "public/private export and content-addressed filenames",
    ],
    "failures": failures,
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
raise SystemExit(0 if not failures else 1)
