"""Bounded native-family audit with protected-Racket label replay."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
ROOT = next(
    candidate for candidate in HOME.parents
    if (candidate / "src" / "arcpuzzles").is_dir() and (candidate / "shared" / "runtime").is_dir()
)
RUNTIME = ROOT / "shared" / "runtime"
sys.path.insert(0, str(ROOT / "src"))

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator  # noqa: E402


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_native():
    path = HOME / "native_family.py"
    spec = importlib.util.spec_from_file_location("_audit_frame_centers_native", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _source_binding() -> dict[str, str]:
    files = [
        HOME / "adapter.py",
        HOME / "canonical.rkt",
        HOME / "native_family.py",
        HOME / "promotion.json",
        HOME / "README.md",
        Path(__file__),
        HOME.parents[1] / "generator.py",
        HOME.parents[1] / "tests" / "test_parametric_family.py",
    ]
    return {
        path.relative_to(ROOT).as_posix(): _sha(path.read_bytes())
        for path in files
    }


def run(output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    native = _load_native()
    modes = ["canonical", "center_chain"]
    python_pairs = 0
    prefixes = 0
    settings_separations = 0
    causal_separations = 0
    rival_rejections = 0
    first_profile_point_sets = set()

    def connect(points_grid, *, vertical_first=False, reverse=False):
        out = [row[:] for row in points_grid]
        points = sorted((r, c) for r, row in enumerate(points_grid) for c, value in enumerate(row) if value)
        if reverse:
            points.reverse()
        for (r1, c1), (r2, c2) in zip(points, points[1:]):
            if vertical_first:
                for r in range(min(r1, r2), max(r1, r2) + 1):
                    if out[r][c1] == 0:
                        out[r][c1] = 1
                for c in range(min(c1, c2), max(c1, c2) + 1):
                    if out[r2][c] == 0:
                        out[r2][c] = 1
            else:
                for c in range(min(c1, c2), max(c1, c2) + 1):
                    if out[r1][c] == 0:
                        out[r1][c] = 1
                for r in range(min(r1, r2), max(r1, r2) + 1):
                    if out[r][c2] == 0:
                        out[r][c2] = 1
        return out

    def seed_position_chain(grid):
        sparse = [[0] * len(grid[0]) for _ in grid]
        for _box, (r, c) in native._frames(grid):
            sparse[r][c] = grid[r][c]
        return native._chain_centers(sparse)

    for seed in range(32):
        full = {
            mode: native.generate(seed, {"mode": mode}, 6, 4)
            for mode in modes
        }
        inputs = {
            mode: [pair["input"] for pair in full[mode]["train"] + full[mode]["test"]]
            for mode in modes
        }
        if inputs["canonical"] != inputs["center_chain"]:
            raise AssertionError("input bank depends on the setting")
        first_output = full["canonical"]["train"][0]["output"]
        first_profile_point_sets.add(tuple(
            (r, c) for r, row in enumerate(first_output) for c, value in enumerate(row) if value
        ))
        if len({json.dumps(grid, separators=(",", ":")) for grid in inputs["canonical"]}) != 10:
            raise AssertionError("episode input bank contains duplicates")
        for demo_count in range(2, 7):
            for query_count in range(1, 5):
                for mode in modes:
                    episode = native.generate(seed, {"mode": mode}, demo_count, query_count)
                    if episode["train"] != full[mode]["train"][:demo_count]:
                        raise AssertionError("demonstration prefix instability")
                    if episode["test"] != full[mode]["test"][:query_count]:
                        raise AssertionError("query prefix instability")
                    prefixes += 1
        for mode in modes:
            for pair in full[mode]["train"] + full[mode]["test"]:
                if pair["output"] != native.solve(pair["input"], mode):
                    raise AssertionError("Python label mismatch")
                python_pairs += 1
        if not all(
            a["output"] != b["output"]
            for a, b in zip(full["canonical"]["train"][:2], full["center_chain"]["train"][:2])
        ):
            raise AssertionError("two demonstrations do not distinguish settings")
        settings_separations += 2
        alt_demos = full["center_chain"]["train"][:2]
        rivals = {
            "vertical_first": lambda grid: connect(native.solve(grid, "canonical"), vertical_first=True),
            "reverse_order": lambda grid: connect(native.solve(grid, "canonical"), reverse=True),
            "seed_positions": seed_position_chain,
        }
        for name, rival in rivals.items():
            if all(rival(pair["input"]) == pair["output"] for pair in alt_demos):
                raise AssertionError(f"plausible rival survived both teaching demonstrations: {name}")
            rival_rejections += 1
        case = full["center_chain"]["test"][0]
        intermediate = native.solve(case["input"], "canonical")
        wrong = [row[:] for row in intermediate]
        points = [(r, c) for r, row in enumerate(wrong) for c, value in enumerate(row) if value]
        if len(points) < 2:
            raise AssertionError("causal case lacks two derived centers")
        # skip-A counterfactual: applying only B to the original frame grid has a
        # different point set and therefore cannot equal the declared result.
        skipped = native._chain_centers(case["input"])
        if skipped == case["output"]:
            raise AssertionError("skip-A counterfactual did not change the output")
        causal_separations += 1

    if len(first_profile_point_sets) < 3:
        raise AssertionError("derived center locations do not vary enough across seeds")

    protected_rows = []
    with _local_imports(RUNTIME, HOME):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            if identity.get("backend") != "racket" or identity.get("protected") is not True:
                raise AssertionError("protected Racket runtime unavailable")
            for seed in (0, 17):
                for mode in modes:
                    settings = {"mode": mode}
                    episode = native.generate(seed, settings, 6, 4)
                    program = native.program(settings)
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = apply(program, copy.deepcopy(pair["input"]))
                            if actual != pair["output"]:
                                raise AssertionError(
                                    f"protected Racket mismatch seed={seed} mode={mode} {split}[{index}]"
                                )
                            protected_rows.append(
                                {
                                    "seed": seed,
                                    "mode": mode,
                                    "split": split,
                                    "index": index,
                                    "input_sha256": _sha(json.dumps(pair["input"], separators=(",", ":")).encode()),
                                    "output_sha256": _sha(json.dumps(actual, separators=(",", ":")).encode()),
                                }
                            )
        finally:
            bridge.close()

    report = {
        "schema": "9df4a42fced1-native-parametric-audit-v1",
        "status": "passed",
        "task_id": "9df4a42fced1",
        "source_binding": _source_binding(),
        "bounded_scope": {
            "seeds": 32,
            "settings": modes,
            "demo_counts": [2, 3, 4, 5, 6],
            "query_counts": [1, 2, 3, 4],
        },
        "checks": {
            "python_labeled_pairs": python_pairs,
            "prefix_requests": prefixes,
            "setting_distinguishing_demonstrations": settings_separations,
            "skip_a_causal_separations": causal_separations,
            "plausible_rival_rejections": rival_rejections,
            "first_profile_center_patterns": len(first_profile_point_sets),
            "protected_racket_labels": len(protected_rows),
        },
        "racket": identity,
        "protected_rows": protected_rows,
        "limits": "Finite declared-setting and constructed-scene audit; not universal rule identifiability or owner acceptance.",
        "owner_accepted": False,
        "training_admitted": False,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.out)
    print(json.dumps({"status": report["status"], **report["checks"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
