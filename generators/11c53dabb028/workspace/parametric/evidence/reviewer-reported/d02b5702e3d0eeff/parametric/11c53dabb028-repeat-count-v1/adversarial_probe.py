#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path.cwd()
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.extraction import _program_body

PROTO_PATH = ROOT / "generators" / "11c53dabb028" / "workspace" / "parametric" / "prototype.py"
spec = importlib.util.spec_from_file_location("adversarial_parametric_11c53dabb028", PROTO_PATH)
assert spec is not None and spec.loader is not None
proto = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = proto
spec.loader.exec_module(proto)

invalid_values = [None, True, False, 0, -1, 3, 1.0, 2.0, float("nan"), "1", [], {}]
validation_failures = []
validation_rejections = 0
for value in invalid_values:
    for args in ((value, 2), (2, value)):
        try:
            proto.program_for(*args)
        except (TypeError, ValueError):
            validation_rejections += 1
        else:
            validation_failures.append(repr(args))

rows = []
all_racket_exact = True
all_rivals_differ = True
all_private_stable = True
all_shapes_bounded = True
bridge = RacketBridge(timeout=20, max_calls_before_restart=32)
try:
    for setting_index, setting in enumerate(proto.SETTINGS):
        for offset in range(4):
            seed = 91000 + setting_index * 100 + offset
            episode = proto.generate_episode(
                seed,
                vertical_repeats=setting[0],
                horizontal_repeats=setting[1],
                n_train=1,
                n_test=1,
            )
            before_public = proto.public_bytes(episode)
            mutated = deepcopy(episode)
            mutated["parameters"] = {"vertical_repeats": 9, "horizontal_repeats": 9}
            mutated["program"] = "private mutation"
            mutated["meta"]["seed"] = -999
            mutated["test"][0]["output"] = [[9]]
            private_stable = proto.public_bytes(mutated) == before_public
            all_private_stable &= private_stable

            body = _program_body(proto.program_for(*setting))
            pair_rows = []
            for split in ("train", "test"):
                pair = episode[split][0]
                grid = pair["input"]
                bridge.define_grid("g", grid)
                got = bridge.eval_text(body)
                exact = got == pair["output"]
                all_racket_exact &= exact
                rivals_differ = all(
                    proto.solve(
                        grid,
                        vertical_repeats=rival[0],
                        horizontal_repeats=rival[1],
                    ) != pair["output"]
                    for rival in proto.SETTINGS
                    if rival != setting
                )
                all_rivals_differ &= rivals_differ
                expected_shape = [setting[0] * len(grid), setting[1] * len(grid[0])]
                actual_shape = [len(got), len(got[0])]
                bounded = actual_shape == expected_shape and max(actual_shape) <= 30
                all_shapes_bounded &= bounded
                pair_rows.append({
                    "split": split,
                    "input_shape": [len(grid), len(grid[0])],
                    "output_shape": actual_shape,
                    "racket_exact": exact,
                    "all_rivals_differ": rivals_differ,
                    "shape_bounded": bounded,
                })
            rows.append({
                "seed": seed,
                "setting": list(setting),
                "private_projection_stable": private_stable,
                "pairs": pair_rows,
            })
finally:
    bridge.shutdown()

report = {
    "schema": "11c53dabb028-repeat-count-adversarial-v1",
    "invalid_values_per_axis": len(invalid_values),
    "validation_attempts": len(invalid_values) * 2,
    "validation_rejections": validation_rejections,
    "validation_failures": validation_failures,
    "episodes": len(rows),
    "pairs": sum(len(row["pairs"]) for row in rows),
    "all_racket_exact": all_racket_exact,
    "all_rivals_differ": all_rivals_differ,
    "all_private_projection_stable": all_private_stable,
    "all_shapes_bounded": all_shapes_bounded,
    "rows": rows,
}
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if all((
    not validation_failures,
    all_racket_exact,
    all_rivals_differ,
    all_private_stable,
    all_shapes_bounded,
)) else 1)
