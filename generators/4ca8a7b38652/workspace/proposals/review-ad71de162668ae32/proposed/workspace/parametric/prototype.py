"""Unapproved task-local count-then-upscale episode prototype.

All retained labels come from the packet's protected Racket bridge. The Python
mirror checks those labels; it is never the label authority. No production
generator interface, canonical rule, or approval metadata is modified here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parent.parent
OFFSETS = (-1, 0, 1)
QUERY_SIDES = (3, 6)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_offset(value: int) -> None:
    if type(value) is not int or value not in OFFSETS:
        raise ValueError("scale_offset must be a literal integer in {-1,0,1}")


def rule_source(scale_offset: int = 0) -> str:
    validate_offset(scale_offset)
    return (HERE / "programs" / f"offset_{scale_offset}.rkt").read_text()


def _generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("prototype_canonical_sampler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode_inputs(*, seed: int, scale_offset: int | None = None,
                   query_side: int = 3) -> tuple[int, list]:
    """Choose one rule per seed, then draw five demos and one query.

    Parameter selection is a stable SHA-256 mapping, independent of sampler RNG
    consumption. Explicit offsets leave the input draws unchanged, permitting
    direct comparisons between rules. The larger query preserves the palette
    while independently shuffling 36 cells, rather than geometrically upscaling
    or tiling the original 3x3 layout.
    """
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(query_side) is not int or query_side not in QUERY_SIDES:
        raise ValueError("query_side must be a literal integer, 3 or 6")
    if scale_offset is None:
        key = hashlib.sha256(f"4ca8a7b38652/scale-offset/v1/{seed}".encode()).digest()
        scale_offset = OFFSETS[int.from_bytes(key, "big") % len(OFFSETS)]
    validate_offset(scale_offset)
    sampler = _generator()
    inputs = [sampler.generate(seed, i, difficulty="hard") for i in range(6)]
    if query_side == 6:
        cells = [value for row in inputs[-1] for value in row] * 4
        rng = random.Random(f"4ca8a7b38652/larger-query/v1/{seed}")
        rng.shuffle(cells)
        inputs[-1] = [cells[i:i + 6] for i in range(0, 36, 6)]
    return scale_offset, inputs


def _upscale(grid: list, factor: int) -> list:
    factor = max(1, factor)
    return [[value for value in row for _ in range(factor)]
            for row in grid for _ in range(factor)]


def mirror(grid: list, scale_offset: int = 0) -> list:
    validate_offset(scale_offset)
    n = len({value for row in grid for value in row} - {0})
    return _upscale(grid, n + scale_offset)


class RacketLabels:
    """Execute exact materialized (rule! ...) text with the protected bridge."""

    def __init__(self):
        self.bridge = None
        self.calls = 0

    def __enter__(self):
        self.bridge = RacketBridge(timeout=10)
        self.bridge.eval_text("(define prototype-rule #f)")
        self.bridge.eval_text("(define (rule! procedure) (set! prototype-rule procedure))")
        return self

    def apply(self, source: str, grid: list) -> list:
        if self.bridge is None:
            raise RuntimeError("use RacketLabels as a context manager")
        self.bridge.eval_text(source)
        self.bridge.define_grid("prototype-input", grid)
        output = self.bridge.eval_text("(prototype-rule prototype-input)")
        self.calls += 1
        return output

    def __exit__(self, exc_type, exc, traceback):
        if self.bridge is not None:
            self.bridge.shutdown()
            self.bridge = None


def score_rivals(labels: RacketLabels, pairs: list) -> dict:
    """Record exact refuting demos; never silently discard a surviving rival."""
    predictions = {
        f"offset_{offset}": [labels.apply(rule_source(offset), pair["input"])
                             for pair in pairs]
        for offset in OFFSETS
    }
    for factor in range(1, 6):
        predictions[f"fixed_{factor}"] = [_upscale(pair["input"], factor) for pair in pairs]
    for name, delta in (("count_all_colors", 0), ("all_colors_minus_one", -1)):
        predictions[name] = [
            _upscale(pair["input"], len({v for row in pair["input"] for v in row}) + delta)
            for pair in pairs
        ]
    result = {}
    for name, outputs in predictions.items():
        refuting = [i for i, output in enumerate(outputs[:-1]) if output != pairs[i]["output"]]
        query_agrees = outputs[-1] == pairs[-1]["output"]
        result[name] = {
            "status": "refuted_by_demos" if refuting else (
                "survived_all" if query_agrees else "ambiguous_query"),
            "refuting_demo_indices": refuting,
            "query_agrees": query_agrees,
            "backend": "racket" if name.startswith("offset_") else "python_rival",
        }
    return result


def build_episode(labels: RacketLabels, *, seed: int, scale_offset: int | None = None,
                  query_side: int = 3) -> tuple[dict, dict]:
    offset, inputs = episode_inputs(seed=seed, scale_offset=scale_offset, query_side=query_side)
    source = rule_source(offset)
    pairs = []
    for grid in inputs:
        output = labels.apply(source, grid)
        if output != mirror(grid, offset):
            raise AssertionError("Racket label disagrees with independent Python mirror")
        if not output or len(output) > 30 or len(output[0]) > 30:
            raise AssertionError("prototype output exceeds ARC 30x30 bound")
        pairs.append({"input": grid, "output": output})
    public = {"train": pairs[:-1], "test": [{"input": inputs[-1]}]}
    private = {
        "schema": "4ca8a7b38652-parametric-prototype-v1",
        "status": "prototype_unapproved",
        "seed": seed,
        "parameters": {"scale_offset": offset},
        "query_side": query_side,
        "label_backend": "racket",
        "rule": {"text": source, "sha256": sha256(source.encode())},
        "source_sha256": {
            "prototype.py": sha256(Path(__file__).read_bytes()),
            "generator.py": sha256((TASK_HOME / "generator.py").read_bytes()),
        },
        "query_outputs": [pairs[-1]["output"]],
        "rival_checks": score_rivals(labels, pairs),
    }
    return public, private


def _json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def retain_episode(out: Path, name: str, public: dict, private: dict) -> dict:
    public_path = out / name / "public/challenge.json"
    private_path = out / name / "private/episode.json"
    _json(public_path, public)
    _json(private_path, private)
    return {"name": name, "public": str(public_path.relative_to(out)),
            "private": str(private_path.relative_to(out)),
            "public_sha256": sha256(public_path.read_bytes()),
            "private_sha256": sha256(private_path.read_bytes()),
            "parameters": private["parameters"], "query_side": private["query_side"],
            "ambiguous_rivals": [name for name, row in private["rival_checks"].items()
                                 if row["status"] == "ambiguous_query"]}


def build_suite(labels: RacketLabels, out: Path) -> dict:
    episodes = []
    for offset in OFFSETS:
        for query_side in QUERY_SIDES:
            public, private = build_episode(labels, seed=23, scale_offset=offset, query_side=query_side)
            episodes.append(retain_episode(out, f"explicit_{offset}_q{query_side}", public, private))
    for seed in range(6):
        public, private = build_episode(labels, seed=seed, query_side=6)
        episodes.append(retain_episode(out, f"seeded_{seed}_q6", public, private))
    witness = [[0, 1, 0], [2, 0, 1], [0, 2, 0]]
    witness_outputs = {str(offset): labels.apply(rule_source(offset), witness) for offset in OFFSETS}
    _json(out / "private/witness.json", {"input": witness, "outputs_by_scale_offset": witness_outputs})
    canonical = canonical_pairs("4ca8a7b38652", root=find_root(__file__))
    parity = [labels.apply(rule_source(0), pair["input"]) == pair["output"] for pair in canonical]
    if not all(parity):
        raise AssertionError("default setting failed canonical label parity")
    report = {
        "schema": "4ca8a7b38652-parametric-suite-v1", "status": "prototype_unapproved",
        "episodes": episodes, "episode_count": len(episodes),
        "demonstrations_per_episode": 5, "queries_per_episode": 1,
        "racket_primary_labels": 6 * len(episodes),
        "racket_parameter_rival_labels": 18 * len(episodes),
        "canonical_label_parity": {"passed": sum(parity), "total": len(parity)},
        "witness_output_sides": {key: len(value) for key, value in witness_outputs.items()},
        "racket_calls": labels.calls,
        "limits": ["finite retained seeds 0..5 plus explicit seed 23",
                   "ordered five-demo one-query episodes; arbitrary rotations not claimed",
                   "6x6 queries are outside the canonical 3x3 teaching manifold",
                   "three parameter rivals and seven named shortcut rivals only",
                   "no production parametric API or approval change"],
        "source_sha256": {path.name: sha256(path.read_bytes()) for path in
                           [Path(__file__), HERE / "README.md", TASK_HOME / "generator.py"]},
        "program_sha256": {str(offset): sha256(rule_source(offset).encode()) for offset in OFFSETS},
    }
    _json(out / "SUMMARY.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--scale-offset", type=int, choices=OFFSETS)
    parser.add_argument("--query-side", type=int, choices=QUERY_SIDES, default=3)
    parser.add_argument("--suite", action="store_true")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("--out must name a new directory to preserve prior evidence")
    with RacketLabels() as labels:
        if args.suite:
            report = build_suite(labels, args.out)
        else:
            public, private = build_episode(labels, seed=args.seed,
                                            scale_offset=args.scale_offset, query_side=args.query_side)
            report = retain_episode(args.out, "episode", public, private)
            _json(args.out / "SUMMARY.json", report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
