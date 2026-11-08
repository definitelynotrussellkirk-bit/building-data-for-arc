#!/usr/bin/env python3
"""Task-local parametric-rule prototype for ARC family 6ecd11f4.

This module is deliberately separate from the selected production generator.
The canonical setting keeps palette entries whose corresponding large block is
filled; the proposed alternative keeps entries whose block is empty.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import importlib.util
import sys
from pathlib import Path


TASK_ID = "4e4fa6c8d4ce"
PARAMETER_SPEC = {
    "name": "mask_mode",
    "values": ("filled", "empty"),
    "default": "filled",
}


def choose_mask_mode(seed: int) -> str:
    """Choose one hidden rule value deterministically for a whole episode."""
    digest = hashlib.sha256(
        f"{TASK_ID}|parametric|mask_mode|{seed}".encode("utf-8")
    ).digest()
    return PARAMETER_SPEC["values"][digest[0] % len(PARAMETER_SPEC["values"])]


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def _load_generator():
    name = f"parametric_runtime_{TASK_ID}_generator"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _validate_mode(mask_mode: str) -> str:
    if mask_mode not in PARAMETER_SPEC["values"]:
        raise ValueError(
            f"mask_mode must be one of {PARAMETER_SPEC['values']}, got {mask_mode!r}"
        )
    return mask_mode


def apply_python(grid: list[list[int]], mask_mode: str) -> list[list[int]]:
    """Reference mirror for either proposed parameter setting."""
    mode = _validate_mode(mask_mode)
    analysis = _load_generator()._analyse(grid)
    side = int(analysis["palette_size"])
    palette = analysis["palette"]
    mask = analysis["mask"]
    keep_filled = mode == "filled"
    return [
        [
            palette[row][col]
            if bool(mask[row][col]) == keep_filled
            else 0
            for col in range(side)
        ]
        for row in range(side)
    ]


def build_episode(
    *,
    seed: int,
    mask_mode: str | None = None,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 3,
    n_test: int = 1,
    labeler=apply_python,
) -> dict[str, object]:
    """Build one complete prototype episode with one fixed hidden rule value."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(start_index) is not int or start_index < 0:
        raise ValueError("start_index must be a nonnegative integer")
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive integer")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive integer")

    mode = choose_mask_mode(seed) if mask_mode is None else _validate_mode(mask_mode)
    generator = _load_generator()
    sample_indices = list(range(start_index, start_index + n_train + n_test))
    pairs: list[dict[str, object]] = []
    for sample_index in sample_indices:
        grid = generator.generate(seed, sample_index, difficulty=difficulty)
        output = labeler(grid, mode)
        pairs.append({"input": grid, "output": output})

    return {
        "schema": "4e4fa6c8d4ce-parametric-episode-v1",
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "meta": {
            "task_id": TASK_ID,
            "prototype": True,
            "parameters": {PARAMETER_SPEC["name"]: mode},
            "seed": seed,
            "difficulty": difficulty,
            "start_index": start_index,
            "sample_indices": sample_indices,
            "input_generator_version": generator.VERSION,
        },
    }


def parameter_rival_findings(episode: dict[str, object]) -> list[str]:
    """Report parameter values that still fit every demonstration."""
    meta = episode.get("meta")
    if not isinstance(meta, dict):
        return ["episode is missing metadata"]
    parameters = meta.get("parameters")
    if not isinstance(parameters, dict):
        return ["episode is missing parameter metadata"]
    chosen = parameters.get(PARAMETER_SPEC["name"])
    try:
        chosen = _validate_mode(chosen)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    demos = episode.get("train")
    if not isinstance(demos, list) or not demos:
        return ["episode needs at least one demonstration"]

    findings: list[str] = []
    for rival_mode in PARAMETER_SPEC["values"]:
        if rival_mode == chosen:
            continue
        rival_fits = True
        for index, pair in enumerate(demos):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                findings.append(f"demo {index} is malformed")
                rival_fits = False
                continue
            if apply_python(pair["input"], rival_mode) != pair["output"]:
                rival_fits = False
        if rival_fits:
            findings.append(
                f"demonstrations do not distinguish mask_mode={chosen!r} "
                f"from {rival_mode!r}"
            )
    return findings


def public_challenge(episode: dict[str, object]) -> dict[str, list[dict[str, object]]]:
    """Strip hidden rule metadata, program text, and query answers."""
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in train
        ],
        "test": [{"input": pair["input"]} for pair in test],
    }


RULE_DIR = HERE.parent / "rules"


def racket_source(mask_mode: str) -> str:
    """Return the materialized Racket authority for one prototype setting."""
    mode = _validate_mode(mask_mode)
    path = RULE_DIR / f"{mode}.rkt"
    if not path.is_file():
        raise FileNotFoundError(f"missing prototype rule source: {path}")
    return path.read_text(encoding="utf-8")


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in grid
    )
    return f"'({rows})"


def _racket_runtime():
    import types

    scripts = types.ModuleType("scripts")
    scripts.__path__ = [str(ROOT / "shared" / "tools")]
    sys.modules.setdefault("scripts", scripts)
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    return RacketBridge, wrap_rule


def apply_racket(grid: list[list[int]], mask_mode: str) -> list[list[int]]:
    """Execute the exact materialized Racket program for one setting."""
    source = racket_source(mask_mode)
    RacketBridge, wrap_rule = _racket_runtime()
    expression = f"({wrap_rule(source)} {_grid_literal(grid)})"
    bridge = RacketBridge(max_calls_before_restart=8)
    try:
        output = bridge.eval_text(expression)
    finally:
        bridge.shutdown()
    if not isinstance(output, list) or not output or not isinstance(output[0], list):
        raise RuntimeError(f"prototype rule returned non-grid output: {output!r}")
    return [[int(value) for value in row] for row in output]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode("utf-8")).hexdigest()[:12]


def _all_pairs(episode: dict[str, object]) -> list[dict[str, object]]:
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    return [*train, *test]


def build_evidence(
    *,
    seed: int,
    difficulty: str = "medium",
    start_index: int = 0,
    n_train: int = 3,
    n_test: int = 1,
) -> dict[str, object]:
    """Execute both Racket variants and retain bounded prototype evidence."""
    generator = _load_generator()
    episodes: dict[str, dict[str, object]] = {}
    parity: dict[str, list[bool]] = {}
    rival_findings: dict[str, list[str]] = {}

    for mode in PARAMETER_SPEC["values"]:
        episode = build_episode(
            seed=seed,
            mask_mode=mode,
            difficulty=difficulty,
            start_index=start_index,
            n_train=n_train,
            n_test=n_test,
            labeler=apply_racket,
        )
        episodes[mode] = episode
        parity[mode] = [
            pair["output"] == apply_python(pair["input"], mode)
            for pair in _all_pairs(episode)
        ]
        rival_findings[mode] = parameter_rival_findings(episode)

    filled_pairs = _all_pairs(episodes["filled"])
    empty_pairs = _all_pairs(episodes["empty"])
    inputs_shared = [
        left["input"] == right["input"]
        for left, right in zip(filled_pairs, empty_pairs, strict=True)
    ]
    witness_index = next(
        index
        for index, (left, right) in enumerate(
            zip(filled_pairs, empty_pairs, strict=True)
        )
        if left["output"] != right["output"]
    )
    witness_filled = filled_pairs[witness_index]
    witness_empty = empty_pairs[witness_index]

    rule_records: dict[str, dict[str, object]] = {}
    for mode in PARAMETER_SPEC["values"]:
        source = racket_source(mode)
        path = RULE_DIR / f"{mode}.rkt"
        rule_records[mode] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": _sha256_text(source),
            "normalized_hash": _normalized_rule_hash(source),
            "text": source,
        }

    filled_hash_matches = (
        rule_records["filled"]["normalized_hash"] == generator.RULE_HASH
    )
    settings_disagree = witness_filled["output"] != witness_empty["output"]
    checks: dict[str, object] = {
        "filled_rule_hash_matches_selected": filled_hash_matches,
        "inputs_shared_across_settings": inputs_shared,
        "racket_python_parity": parity,
        "parameter_rival_findings": rival_findings,
        "settings_disagree_on_witness": settings_disagree,
    }
    checks["all_passed"] = bool(
        filled_hash_matches
        and all(inputs_shared)
        and all(all(rows) for rows in parity.values())
        and all(not findings for findings in rival_findings.values())
        and settings_disagree
    )

    return {
        "schema": "4e4fa6c8d4ce-parametric-evidence-v1",
        "task_id": TASK_ID,
        "status": "proposed",
        "parameter": {
            **PARAMETER_SPEC,
            "scope": "chosen once per episode",
            "input_constraints": [
                "the block mask contains both filled and empty logical cells",
                "the dense palette contains only nonzero values",
                "the mask and palette use the same logical coordinates",
            ],
            "invariant_reasoning": [
                "identify the uniquely most-common shape colour",
                "recover the large block mask and dense palette",
                "map corresponding mask and palette coordinates",
                "copy selected palette cells and write zero elsewhere",
            ],
        },
        "replay": {
            "seed": seed,
            "difficulty": difficulty,
            "start_index": start_index,
            "n_train": n_train,
            "n_test": n_test,
        },
        "sources": {
            "prototype": {
                "path": str(HERE.relative_to(ROOT)),
                "sha256": _sha256_file(HERE),
            },
            "selected_generator": {
                "path": str(GENERATOR_PATH.relative_to(ROOT)),
                "sha256": _sha256_file(GENERATOR_PATH),
                "version": generator.VERSION,
                "rule_hash": generator.RULE_HASH,
            },
            "rules": rule_records,
        },
        "episodes": episodes,
        "disagreement_witness": {
            "pair_offset": witness_index,
            "sample_index": start_index + witness_index,
            "input": witness_filled["input"],
            "outputs": {
                "filled": witness_filled["output"],
                "empty": witness_empty["output"],
            },
        },
        "checks": checks,
        "limitations": [
            "This is a task-local prototype, not a selected or approved production rule.",
            "Evidence covers two settings and one four-pair episode per setting, not every seed.",
            "The input sampler is the fixed canonical generator; only the executed rule varies.",
            "The hidden parameter is identifiable only when demonstrations include mixed masks, which this sampler enforces.",
        ],
    }


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def write_artifacts(
    evidence: dict[str, object],
    *,
    out_path: Path,
    public_dir: Path,
) -> dict[str, object]:
    """Write private evidence plus two parameter-blind public challenges."""
    result = copy.deepcopy(evidence)
    episodes = result.get("episodes")
    if not isinstance(episodes, dict):
        raise ValueError("evidence must contain an episodes mapping")

    public_dir.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict[str, object]] = {}
    for label, mode in (("episode-a", "filled"), ("episode-b", "empty")):
        episode = episodes.get(mode)
        if not isinstance(episode, dict):
            raise ValueError(f"evidence is missing the {mode!r} episode")
        challenge = public_challenge(episode)
        path = (public_dir / f"{label}.json").resolve()
        text = json.dumps(challenge, indent=2) + "\n"
        path.write_text(text, encoding="utf-8")
        records[label] = {
            # The mapping is private evidence; it is not written into the challenge.
            "parameter_value": mode,
            "path": _portable_path(path),
            "absolute_path": str(path),
            "sha256": _sha256_text(text),
        }

    result["public_challenges"] = records
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result["evidence_path"] = _portable_path(out_path)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build Racket-checked mask-mode prototype evidence."
    )
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=1)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--public-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    evidence = build_evidence(
        seed=args.seed,
        difficulty=args.difficulty,
        start_index=args.start_index,
        n_train=args.n_train,
        n_test=args.n_test,
    )
    evidence["execution"] = {
        "command": [sys.executable, *sys.argv],
        "working_directory": str(Path.cwd()),
    }
    written = write_artifacts(
        evidence, out_path=args.out, public_dir=args.public_dir
    )
    print(Path(args.out).resolve())
    return 0 if written["checks"]["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
