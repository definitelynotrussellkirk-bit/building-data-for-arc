"""Bounded native-family audit with protected-Racket labels and skip-A replay."""
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
    spec = importlib.util.spec_from_file_location("_audit_l_completion_native", path)
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
        HOME / "preflight_compat.py",
        Path(__file__),
        HOME.parents[1] / "generator.py",
        HOME.parents[1] / "tests" / "test_generator_fad48869c581.py",
        HOME.parents[1] / "tests" / "test_parametric_family.py",
        HOME.parents[1] / "tests" / "test_preflight_compat.py",
    ]
    return {
        path.relative_to(ROOT).as_posix(): _sha(path.read_bytes())
        for path in files
    }


def _skip_a_program(native) -> str:
    needle = f"(completed {native._CANONICAL_BODY})"
    if native.SQUARE_HALO.count(needle) != 1:
        raise AssertionError("cannot derive exact skip-A counterfactual")
    return native.SQUARE_HALO.replace(needle, "(completed g)", 1)


def _fixed_color_halo(native, grid):
    completed = native.solve(grid, "canonical")
    out = [row[:] for row in completed]
    h, w = len(out), len(out[0])
    for r, c, _color in native._solid_squares(completed):
        for rr in range(max(0, r - 1), min(h, r + 3)):
            for cc in range(max(0, c - 1), min(w, c + 3)):
                if out[rr][cc] == 0:
                    out[rr][cc] = 1
    return out


def _three_by_three(native, grid):
    completed = native.solve(grid, "canonical")
    out = [row[:] for row in completed]
    h, w = len(out), len(out[0])
    for r, c, color in native._solid_squares(completed):
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if out[rr][cc] == 0:
                    out[rr][cc] = color
    return out


def _source_color_only(native, grid):
    completed = native.solve(grid, "canonical")
    out = [row[:] for row in completed]
    h, w = len(out), len(out[0])
    for r, c, color in native._solid_squares(completed):
        for rr, cc in ((r - 1, c), (r - 1, c + 1), (r + 2, c), (r + 2, c + 1)):
            if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
                out[rr][cc] = color
    return out


def run(output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    native = _load_native()
    modes = ["canonical", "square_halo"]
    python_pairs = 0
    prefixes = 0
    settings_separations = 0
    causal_separations = 0
    rival_rejections = 0
    first_profile_fire_sets = set()

    for seed in range(32):
        full = {
            mode: native.generate(seed, {"mode": mode}, 6, 4)
            for mode in modes
        }
        inputs = {
            mode: [pair["input"] for pair in full[mode]["train"] + full[mode]["test"]]
            for mode in modes
        }
        if inputs["canonical"] != inputs["square_halo"]:
            raise AssertionError("input bank depends on the setting")
        if len({json.dumps(grid, separators=(",", ":")) for grid in inputs["canonical"]}) != 10:
            raise AssertionError("episode input bank contains duplicates")
        first = full["canonical"]["train"][0]
        first_profile_fire_sets.add(tuple(
            (r, c)
            for r, (before, after) in enumerate(zip(first["input"], first["output"]))
            for c, (a, b) in enumerate(zip(before, after))
            if a != b
        ))
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
            for a, b in zip(full["canonical"]["train"][:2], full["square_halo"]["train"][:2])
        ):
            raise AssertionError("two demonstrations do not distinguish settings")
        settings_separations += 2

        alt_demos = full["square_halo"]["train"][:2]
        rivals = {
            "canonical_only": lambda grid: native.solve(grid, "canonical"),
            "fixed_color_halo": lambda grid: _fixed_color_halo(native, grid),
            "three_by_three": lambda grid: _three_by_three(native, grid),
            "cardinal_only": lambda grid: _source_color_only(native, grid),
        }
        for name, rival in rivals.items():
            if all(rival(pair["input"]) == pair["output"] for pair in alt_demos):
                raise AssertionError(f"plausible rival survived both teaching demonstrations: {name}")
            rival_rejections += 1

        case = full["square_halo"]["test"][0]
        intermediate = native.solve(case["input"], "canonical")
        if not native._solid_squares(intermediate):
            raise AssertionError("Stage A did not create a square")
        if native._solid_squares(case["input"]):
            raise AssertionError("original input already exposes Stage-B trigger")
        if native._halo_squares(case["input"]) == case["output"]:
            raise AssertionError("skip-A counterfactual did not change the output")
        causal_separations += 1

    if len(first_profile_fire_sets) < 5:
        raise AssertionError("missing-corner locations do not vary enough across seeds")

    protected_rows = []
    counterfactual_rows = []
    skip_a = _skip_a_program(native)
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
                alternative = native.generate(seed, {"mode": "square_halo"}, 6, 4)
                for split in ("train", "test"):
                    for index, pair in enumerate(alternative[split]):
                        wrong = apply(skip_a, copy.deepcopy(pair["input"]))
                        if wrong == pair["output"]:
                            raise AssertionError(
                                f"protected skip-A matched seed={seed} {split}[{index}]"
                            )
                        counterfactual_rows.append(
                            {
                                "seed": seed,
                                "split": split,
                                "index": index,
                                "wrong_output_sha256": _sha(json.dumps(wrong, separators=(",", ":")).encode()),
                                "declared_output_sha256": _sha(json.dumps(pair["output"], separators=(",", ":")).encode()),
                            }
                        )
        finally:
            bridge.close()

    report = {
        "schema": "fad48869c581-native-parametric-audit-v1",
        "status": "passed",
        "task_id": "fad48869c581",
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
            "first_profile_fire_patterns": len(first_profile_fire_sets),
            "protected_racket_labels": len(protected_rows),
            "protected_racket_counterfactuals": len(counterfactual_rows),
        },
        "racket": identity,
        "protected_rows": protected_rows,
        "counterfactual_rows": counterfactual_rows,
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
