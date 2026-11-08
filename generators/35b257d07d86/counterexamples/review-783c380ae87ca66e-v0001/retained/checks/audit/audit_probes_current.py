from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path.cwd()
OUT = REPO.parent / "checks" / "audit"
TASKS = ("35b257d07d86", "8dafcfb1101f")
BANDS = ("easy", "medium", "hard")
PER_BAND = 100


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    name = f"audit_generator_{task_id}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module, path


def canonical(task_id: str) -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        obj = json.loads(line)
        if obj.get("task_id") == task_id:
            return obj
    raise KeyError(task_id)


def apply_35(g: list[list[int]], mod) -> list[list[int]]:
    key = mod._find_key(g)
    if key is None:
        return deepcopy(g)
    r0, c0, kh = key
    pairs = [(g[r0 + i][c0], g[r0 + i][c0 + 1]) for i in range(kh)]
    out = deepcopy(g)
    for r, row in enumerate(g):
        for c, value in enumerate(row):
            if r0 <= r < r0 + kh and c0 <= c <= c0 + 1:
                continue
            v = value
            for left, right in pairs:
                if v == left:
                    v = right
            out[r][c] = v
    return out


def terminal_rival_35(g: list[list[int]], mod) -> list[list[int]]:
    key = mod._find_key(g)
    if key is None:
        return deepcopy(g)
    r0, c0, kh = key
    key_colors = {
        g[r0 + i][c]
        for i in range(kh)
        for c in (c0, c0 + 1)
    }
    terminal = g[r0 + kh - 1][c0 + 1]
    out = deepcopy(g)
    for r, row in enumerate(g):
        for c, value in enumerate(row):
            if r0 <= r < r0 + kh and c0 <= c <= c0 + 1:
                continue
            if value in key_colors:
                out[r][c] = terminal
    return out


def marker_delta(g: list[list[int]]) -> tuple[int, int]:
    src = next((r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 1)
    dst = next((r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 2)
    return dst[0] - src[0], dst[1] - src[1]


def apply_8(g: list[list[int]], absolute: bool = False) -> list[list[int]]:
    h, w = len(g), len(g[0])
    dr, dc = marker_delta(g)
    if absolute:
        dr, dc = abs(dr), abs(dc)
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if v in (0, 1, 2):
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = v
    return out


def audit_35() -> None:
    task = "35b257d07d86"
    mod, source = load_generator(task)
    total = valid = rival_matches = errors = 0
    self_check_failures = 0
    first_witness = None
    first_self_check_failure = None
    band_counts = {}
    for bidx, band in enumerate(BANDS):
        b = {"requested": PER_BAND, "generated": 0, "errors": 0, "self_check_failures": 0, "rival_matches": 0}
        for i in range(PER_BAND):
            total += 1
            try:
                g = mod.generate(351000 + bidx * 1000 + i, i, difficulty=band)
            except Exception as exc:
                errors += 1; b["errors"] += 1
                continue
            b["generated"] += 1
            issues = mod.self_check(g, difficulty=band)
            if issues:
                self_check_failures += 1; b["self_check_failures"] += 1
                if first_self_check_failure is None:
                    first_self_check_failure = {"band": band, "sample_index": i, "input": g, "issues": issues}
            else:
                valid += 1
            intended = apply_35(g, mod)
            rival = terminal_rival_35(g, mod)
            if intended == rival:
                rival_matches += 1; b["rival_matches"] += 1
                if first_witness is None and intended != g:
                    first_witness = {
                        "band": band,
                        "seed": 351000 + bidx * 1000 + i,
                        "sample_index": i,
                        "input": g,
                        "intended_python": intended,
                        "terminal_color_rival": rival,
                        "self_check": issues,
                    }
        band_counts[band] = b

    canon = canonical(task)
    canonical_matches = 0
    first_canonical_disagreement = None
    for idx, pair in enumerate(canon["train"]):
        rival = terminal_rival_35(pair["input"], mod)
        if rival == pair["output"]:
            canonical_matches += 1
        elif first_canonical_disagreement is None:
            first_canonical_disagreement = {
                "pair_index": idx,
                "input": pair["input"],
                "canonical_output": pair["output"],
                "terminal_color_rival": rival,
            }

    result = {
        "schema": "arcpuzzles-adversarial-audit-probe-v1",
        "task_id": task,
        "generator_sha256": sha256(source),
        "generator_version": getattr(mod, "VERSION", None),
        "sampler": {"bands": list(BANDS), "per_band": PER_BAND, "total_requested": total},
        "generated": total - errors,
        "generation_errors": errors,
        "self_check_valid": valid,
        "self_check_failures": self_check_failures,
        "terminal_color_rival_matches": rival_matches,
        "canonical_train_pairs": len(canon["train"]),
        "terminal_color_rival_canonical_matches": canonical_matches,
        "band_counts": band_counts,
        "finding": "generated chain tables collapse every key color outside the key to the terminal right-hand color, so a terminal-color shortcut matches the sampled generated labels but not the canonical ordered substitution task",
    }
    outdir = OUT / task
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    (outdir / "generated_match.json").write_text(json.dumps(first_witness, indent=2) + "\n")
    (outdir / "canonical_counterexample.json").write_text(json.dumps(first_canonical_disagreement, indent=2) + "\n")
    if first_self_check_failure is not None:
        (outdir / "self_check_failure.json").write_text(json.dumps(first_self_check_failure, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


def audit_8() -> None:
    task = "8dafcfb1101f"
    mod, source = load_generator(task)
    total = errors = self_check_failures = 0
    nonnegative_both = abs_rival_matches = 0
    deltas: dict[str, int] = {}
    first_witness = None
    band_counts = {}
    for bidx, band in enumerate(BANDS):
        b = {"requested": PER_BAND, "generated": 0, "errors": 0, "self_check_failures": 0, "nonnegative_both": 0, "abs_rival_matches": 0}
        for i in range(PER_BAND):
            total += 1
            try:
                g = mod.generate(861000 + bidx * 1000 + i, i, difficulty=band)
            except Exception:
                errors += 1; b["errors"] += 1
                continue
            b["generated"] += 1
            issues = mod.self_check(g, difficulty=band)
            if issues:
                self_check_failures += 1; b["self_check_failures"] += 1
            dr, dc = marker_delta(g)
            deltas[f"{dr},{dc}"] = deltas.get(f"{dr},{dc}", 0) + 1
            if dr >= 0 and dc >= 0:
                nonnegative_both += 1; b["nonnegative_both"] += 1
            intended = apply_8(g)
            rival = apply_8(g, absolute=True)
            if intended == rival:
                abs_rival_matches += 1; b["abs_rival_matches"] += 1
                if first_witness is None and dr > 0 and dc > 0:
                    first_witness = {
                        "band": band,
                        "seed": 861000 + bidx * 1000 + i,
                        "sample_index": i,
                        "delta": [dr, dc],
                        "input": g,
                        "intended_python": intended,
                        "absolute_vector_rival": rival,
                        "self_check": issues,
                    }
        band_counts[band] = b

    canon = canonical(task)
    canonical_train = []
    canonical_train_matches = 0
    for idx, pair in enumerate(canon["train"]):
        dr, dc = marker_delta(pair["input"])
        rival = apply_8(pair["input"], absolute=True)
        match = rival == pair["output"]
        canonical_train_matches += int(match)
        canonical_train.append({"pair_index": idx, "delta": [dr, dc], "absolute_vector_rival_matches": match})
    test = canon["test"]
    test_delta = marker_delta(test["input"])
    test_rival = apply_8(test["input"], absolute=True)
    test_match = test_rival == test["output"]
    counterexample = {
        "split": "canonical_test",
        "delta": list(test_delta),
        "input": test["input"],
        "canonical_output": test["output"],
        "absolute_vector_rival": test_rival,
        "rival_matches": test_match,
    }

    result = {
        "schema": "arcpuzzles-adversarial-audit-probe-v1",
        "task_id": task,
        "generator_sha256": sha256(source),
        "generator_version": getattr(mod, "VERSION", None),
        "sampler": {"bands": list(BANDS), "per_band": PER_BAND, "total_requested": total},
        "generated": total - errors,
        "generation_errors": errors,
        "self_check_failures": self_check_failures,
        "nonnegative_row_and_col_deltas": nonnegative_both,
        "absolute_vector_rival_matches": abs_rival_matches,
        "distinct_deltas": len(deltas),
        "delta_histogram": dict(sorted(deltas.items())),
        "canonical_train": canonical_train,
        "absolute_vector_rival_canonical_train_matches": canonical_train_matches,
        "canonical_test_delta": list(test_delta),
        "absolute_vector_rival_canonical_test_matches": test_match,
        "band_counts": band_counts,
        "finding": "the sampler always places source above-left of destination, so an absolute-vector/down-right shortcut matches generated data and both visible canonical demonstrations, but fails the canonical query whose horizontal displacement is leftward",
    }
    outdir = OUT / task
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    (outdir / "generated_match.json").write_text(json.dumps(first_witness, indent=2) + "\n")
    (outdir / "canonical_test_counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    audit_35()
    audit_8()
