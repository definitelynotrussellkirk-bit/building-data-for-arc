"""Bounded protected-Racket audit for the repeated-completion prototype.

This is source-bound authoring evidence, not owner acceptance, a universal
identifiability proof, or training admission.  Run it through review.py so the
same-checkout protected Racket runtime is selected.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK_ID = "a286b2610efc"
HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ROOT = HERE.parents[3]
for dependency in (ROOT / "src", ROOT / "shared/runtime"):
    if str(dependency) not in sys.path:
        sys.path.insert(0, str(dependency))

from arcpuzzles.parametric_worker import evaluate_contract, _real_evaluator
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id


SETTINGS = ({"rounds": 1}, {"rounds": 2})

PASS_LAMBDA = """(lambda (src) (let ((after-h (for*/fold ((out src)) ((r (in-range (rows src))) (c (in-range (- (cols src) 2)))) (let ((a (at src r c)) (b (at src r (+ c 1))) (d (at src r (+ c 2)))) (cond ((and (= a 0) (not (= b 0)) (= b d)) (set-cell out r c b)) ((and (not (= a 0)) (= a b) (= d 0)) (set-cell out r (+ c 2) a)) (else out)))))) (for*/fold ((out after-h)) ((r (in-range (- (rows src) 2))) (c (in-range (cols src)))) (let ((a (at src r c)) (b (at src (+ r 1) c)) (d (at src (+ r 2) c))) (cond ((and (= a 0) (not (= b 0)) (= b d)) (set-cell out r c b)) ((and (not (= a 0)) (= a b) (= d 0)) (set-cell out (+ r 2) c a)) (else out))))))"""

HORIZONTAL_PASS_LAMBDA = """(lambda (src) (for*/fold ((out src)) ((r (in-range (rows src))) (c (in-range (- (cols src) 2)))) (let ((a (at src r c)) (b (at src r (+ c 1))) (d (at src r (+ c 2)))) (cond ((and (= a 0) (not (= b 0)) (= b d)) (set-cell out r c b)) ((and (not (= a 0)) (= a b) (= d 0)) (set-cell out r (+ c 2) a)) (else out)))))"""

VERTICAL_PASS_LAMBDA = """(lambda (src) (for*/fold ((out src)) ((r (in-range (- (rows src) 2))) (c (in-range (cols src)))) (let ((a (at src r c)) (b (at src (+ r 1) c)) (d (at src (+ r 2) c))) (cond ((and (= a 0) (not (= b 0)) (= b d)) (set-cell out r c b)) ((and (not (= a 0)) (= a b) (= d 0)) (set-cell out (+ r 2) c a)) (else out)))))"""

ONE_SIDED = """(rule! (let ((after-h (for*/fold ((out g)) ((r (in-range (rows g))) (c (in-range (- (cols g) 1)))) (let ((a (at g r c)) (b (at g r (+ c 1)))) (if (and (not (= a 0)) (= a b)) (if (and (< (+ c 2) (cols g)) (= (at g r (+ c 2)) 0)) (set-cell out r (+ c 2) a) (if (and (> c 0) (= (at g r (- c 1)) 0)) (set-cell out r (- c 1) a) out)) out))))) (for*/fold ((out after-h)) ((r (in-range (- (rows g) 1))) (c (in-range (cols g)))) (let ((a (at g r c)) (b (at g (+ r 1) c))) (if (and (not (= a 0)) (= a b)) (if (and (< (+ r 2) (rows g)) (= (at g (+ r 2) c) 0)) (set-cell out (+ r 2) c a) (if (and (> r 0) (= (at g (- r 1) c) 0)) (set-cell out (- r 1) c a) out)) out)))))"""


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def load_adapter():
    spec = importlib.util.spec_from_file_location("_a286b2610efc_parametric_audit", HERE / "adapter.py")
    if spec is None or spec.loader is None:
        raise ImportError("cannot load adjacent adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rivals(adapter) -> dict[str, str]:
    """Finite plausible alternatives used only for bounded self-review."""
    three = f"(rule! (let ((pass {PASS_LAMBDA})) (pass (pass (pass g)))))"
    horizontal_second = (
        f"(rule! (let ((pass {PASS_LAMBDA}) (half {HORIZONTAL_PASS_LAMBDA})) "
        "(half (pass g))))"
    )
    vertical_second = (
        f"(rule! (let ((pass {PASS_LAMBDA}) (half {VERTICAL_PASS_LAMBDA})) "
        "(half (pass g))))"
    )
    result = {
        "one_sided_completion": ONE_SIDED,
        "one_round": adapter.program({"rounds": 1}),
        "two_rounds": adapter.program({"rounds": 2}),
        "three_rounds": three,
        "horizontal_second_round_only": horizontal_second,
        "vertical_second_round_only": vertical_second,
    }
    if len(set(result.values())) != len(result):
        raise AssertionError("finite rival programs must be source-distinct")
    for source in result.values():
        wrap_rule(source)
    return result


def census(adapter) -> dict:
    failures = []
    succeeded = 0
    for seed in range(12):
        paired: dict[int, list[str]] = {}
        for setting in SETTINGS:
            for demos in (2, 3, 6):
                request = {"seed": seed, "settings": setting, "demos": demos, "queries": 4}
                try:
                    episode = adapter.generate(**request)
                    assert len(episode["train"]) == demos and len(episode["test"]) == 4
                    inputs = [
                        json.dumps(pair["input"], separators=(",", ":"))
                        for split in ("train", "test")
                        for pair in episode[split]
                    ]
                    assert len(inputs) == len(set(inputs))
                    shorter = adapter.generate(seed, setting, 2, 1)
                    assert shorter["train"] == episode["train"][:2]
                    assert shorter["test"] == episode["test"][:1]
                    if setting["rounds"] == 1:
                        paired[demos] = inputs
                    else:
                        assert paired[demos] == inputs
                    assert all(
                        a["output"] != b["output"]
                        for a, b in zip(
                            adapter.generate(seed, {"rounds": 1}, 2, 1)["train"],
                            adapter.generate(seed, {"rounds": 2}, 2, 1)["train"],
                        )
                    )
                    succeeded += 1
                except Exception as exc:  # retained as exact bounded failure evidence
                    failures.append({**request, "error": f"{type(exc).__name__}: {exc}"})
    return {
        "requested": 72,
        "succeeded": succeeded,
        "failed": len(failures),
        "failures": failures,
        "scope": (
            "Python construction, count, prefix, distinct-input, paired-input and "
            "two-demo setting-separation checks over 12 seeds. Protected labels are separate."
        ),
    }


def export_views(adapter, episodes: list[dict]) -> tuple[dict[str, bytes], dict]:
    public: dict[str, bytes] = {}
    private = []
    for episode in episodes:
        if episode["seed"] != 0 or len(episode["train"]) != 3:
            continue
        views = []
        for query_index, pair in enumerate(episode["test"]):
            view = {"train": episode["train"], "test": [pair]}
            raw = public_challenge_bytes(view)
            identifier = public_challenge_id(view)
            assert sha(raw) == identifier
            decoded = json.loads(raw)
            assert set(decoded) == {"train", "test"}
            assert len(decoded["test"]) == 1 and set(decoded["test"][0]) == {"input"}
            assert all(set(row) == {"input", "output"} for row in decoded["train"])
            mutated = copy.deepcopy(view)
            mutated.update({
                "seed": 999,
                "settings": {"rounds": "redacted"},
                "program_solution": "private",
                "future_queries": [],
            })
            mutated["test"][0]["output"] = [[9]]
            assert public_challenge_bytes(mutated) == raw
            assert public_challenge_id(mutated) == identifier
            if query_index == 0:
                single = adapter.generate(0, episode["settings"], 3, 1)
                assert public_challenge_bytes(single) == raw
            public[identifier] = raw
            views.append({
                "query_index": query_index,
                "public_id": identifier,
                "path": f"public/{identifier}.json",
            })
        private.append({
            "settings": episode["settings"],
            "seed": episode["seed"],
            "demos": len(episode["train"]),
            "views_in_private_order": views,
        })
    assert len(private) == 2 and len(public) == 8
    return public, {
        "episodes": private,
        "checked": [
            "one visible query per view",
            "first view byte-identical to a single-query generation",
            "opaque SHA256 names depend only on visible bytes",
            "private settings, programs, future inputs and query answers do not affect IDs",
        ],
        "consumer_instruction": (
            "Select one view per turn using this private order. Never expose this map, "
            "directory listings, future views, total query count, programs or query labels."
        ),
    }


def grid_stats(grid: list[list[int]]) -> dict:
    height, width = len(grid), len(grid[0])
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return {
        "height": height,
        "width": width,
        "nonzero_cells": len(nonzero),
        "row_extent": [min(r for r, _ in nonzero), max(r for r, _ in nonzero)],
        "column_extent": [min(c for _, c in nonzero), max(c for _, c in nonzero)],
        "occupied_quadrants": len({(r >= height / 2, c >= width / 2) for r, c in nonzero}),
    }


def run(out: Path) -> int:
    if not out.resolve().is_relative_to((HERE / "evidence").resolve()):
        raise ValueError("evidence output must stay under this task's parametric/evidence directory")
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"choose a fresh evidence directory: {out}")

    adapter = load_adapter()
    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    source_paths = [
        HERE / "adapter.py",
        HERE / "audit.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HOME / "generator.py",
        HOME / "tests/test_native_parametric.py",
    ]
    source_hashes = {
        str(path.relative_to(ROOT)): sha(path.read_bytes()) for path in source_paths
    }

    jobs = [
        {"seed": seed, "settings": setting, "demos": demos, "queries": 4}
        for seed in (0, 17)
        for setting in SETTINGS
        for demos in (2, 3, 6)
    ]
    execution = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert execution["racket"]["backend"] == "racket"
    assert execution["racket"]["protected"] is True
    public, export_map = export_views(adapter, execution["episodes"])
    census_result = census(adapter)

    rival_programs = rivals(adapter)
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    extra_evaluations = 0

    def execute(source: str, grid: list[list[int]]) -> list[list[int]]:
        nonlocal extra_evaluations
        extra_evaluations += 1
        value = apply(source, grid)
        assert type(value) is list and len(value) == len(grid)
        assert all(
            type(row) is list
            and len(row) == len(grid[0])
            and all(type(cell) is int and 0 <= cell <= 9 for cell in row)
            for row in value
        )
        return value

    teaching = []
    unresolved = []
    boundary = []
    canonical_checks = []
    try:
        for episode_index, episode in enumerate(execution["episodes"]):
            if len(episode["train"]) != 2:
                continue
            selected_hash = sha(episode["program"].encode("utf-8"))
            rows = []
            for name, source in rival_programs.items():
                if sha(source.encode("utf-8")) == selected_hash:
                    continue
                refutation = None
                for demo_index, pair in enumerate(episode["train"]):
                    output = execute(source, pair["input"])
                    if output != pair["output"]:
                        refutation = {
                            "demo_index": demo_index,
                            "input": pair["input"],
                            "reference_output": pair["output"],
                            "rival_output": output,
                        }
                        break
                row = {
                    "name": name,
                    "program": source,
                    "program_sha256": sha(source.encode("utf-8")),
                }
                if refutation is not None:
                    row.update({"status": "refuted_by_visible_demo", "case": refutation})
                else:
                    disagreements = []
                    for query_index, pair in enumerate(episode["test"]):
                        output = execute(source, pair["input"])
                        if output != pair["output"]:
                            disagreements.append({
                                "query_index": query_index,
                                "input": pair["input"],
                                "reference_output": pair["output"],
                                "rival_output": output,
                            })
                    row.update({
                        "status": "survives_demonstrations",
                        "query_disagreements": disagreements,
                    })
                    unresolved.append({
                        "seed": episode["seed"],
                        "settings": episode["settings"],
                        "rival": name,
                        "query_disagreement_count": len(disagreements),
                    })
                rows.append(row)
            teaching.append({
                "episode_index": episode_index,
                "seed": episode["seed"],
                "settings": episode["settings"],
                "demos_used": 2,
                "rivals": rows,
                "longer_demo_result": "The same first two demonstrations are prefixes of counts 3 and 6.",
            })

        for height, width in ((14, 14), (14, 30), (30, 14), (30, 30)):
            grid = adapter.sample_input(17, "test", 3, height=height, width=width)
            stats = grid_stats(grid)
            assert stats["row_extent"] == [0, height - 1]
            assert stats["column_extent"] == [0, width - 1]
            assert stats["occupied_quadrants"] == 4
            if height == width == 30:
                assert stats["nonzero_cells"] >= 28
            for setting in SETTINGS:
                source = adapter.program(setting)
                output = execute(source, grid)
                assert output == adapter.transform(grid, setting)
                boundary.append({
                    **stats,
                    "settings": setting,
                    "input": grid,
                    "output": output,
                    "program_sha256": sha(source.encode("utf-8")),
                    "first_pass_added": sum(
                        grid[r][c] != adapter.complete_once(grid)[r][c]
                        for r in range(height) for c in range(width)
                    ),
                    "second_pass_added": sum(
                        adapter.complete_once(grid)[r][c]
                        != adapter.transform(grid, {"rounds": 2})[r][c]
                        for r in range(height) for c in range(width)
                    ),
                })

        canonical_row = next(
            json.loads(line)
            for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text(encoding="utf-8").splitlines()
            if json.loads(line).get("task_id") == TASK_ID
        )
        assert canonical_row["program_solution"] == canonical == adapter.program({"rounds": 1})
        for split in ("train", "test"):
            pairs = canonical_row[split]
            if isinstance(pairs, dict):
                pairs = [pairs]
            for pair_index, pair in enumerate(pairs):
                output = execute(canonical, pair["input"])
                assert output == pair["output"] == adapter.transform(pair["input"], {"rounds": 1})
                canonical_checks.append({
                    "split": split,
                    "pair_index": pair_index,
                    "input": pair["input"],
                    "output": output,
                })
    finally:
        bridge.close()

    status = "pass" if not unresolved and census_result["failed"] == 0 else "needs_repair"
    summary = {
        "schema": "arcpuzzles-task-local-authoring-audit-v1",
        "task_id": TASK_ID,
        "status": status,
        "source_hashes": source_hashes,
        "racket": identity,
        "native_jobs": len(execution["episodes"]),
        "native_labels": sum(row["label_count"] for row in execution["checks"]),
        "native_racket_evaluations": execution["racket_evaluations"],
        "additional_racket_evaluations": extra_evaluations,
        "teaching_prefixes": len(teaching),
        "rival_checks": sum(len(row["rivals"]) for row in teaching),
        "refuted_rival_checks": sum(
            rival["status"] == "refuted_by_visible_demo"
            for row in teaching for rival in row["rivals"]
        ),
        "unresolved_rivals": unresolved,
        "boundary_labels": len(boundary),
        "canonical_labels": len(canonical_checks),
        "public_views": len(public),
        "sampling": census_result,
        "limits": (
            "Finite rival set, two qualification seeds and bounded Python census only; "
            "not universal uniqueness, measured training gain, owner acceptance or training admission."
        ),
    }

    dump(out / "execution.json", execution)
    dump(out / "teaching.json", {
        "source_hashes": source_hashes,
        "racket": identity,
        "prefixes": teaching,
        "scope": (
            "Every rival is run only against visible demonstrations first. Query outputs are "
            "inspected only after full demonstration survival; execution errors are fatal."
        ),
    })
    dump(out / "boundary.json", {
        "source_hashes": source_hashes,
        "racket": identity,
        "cases": boundary,
    })
    dump(out / "canonical.json", {
        "source_hashes": source_hashes,
        "racket": identity,
        "cases": canonical_checks,
    })
    dump(out / "private-export-map.json", export_map)
    for identifier, raw in public.items():
        path = out / "public" / f"{identifier}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    dump(out / "summary.json", summary)
    print(json.dumps({
        key: summary[key]
        for key in (
            "status", "native_jobs", "native_labels", "native_racket_evaluations",
            "additional_racket_evaluations", "rival_checks", "refuted_rival_checks",
            "unresolved_rivals", "boundary_labels", "canonical_labels", "public_views",
            "sampling",
        )
    }, sort_keys=True))
    return 0 if status == "pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "evidence/current")
    args = parser.parse_args()
    return run(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
