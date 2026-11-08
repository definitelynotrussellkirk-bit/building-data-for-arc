#!/usr/bin/env python3
"""Episode-level fill-color prototype for ARC task ad5998ad11d6.

The selected production task remains fixed to the canonical color 4.  This
separate authoring prototype chooses one fill color per episode, instantiates
an exact Racket rule, and uses that same rule for all three demonstrations and
the held-out query.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "ad5998ad11d6"
ALLOWED_FILL_COLORS = (4, 2)
DEFAULT_FILL_COLOR = 4
_CANONICAL_CALL = "(fill-all-enclosed g 4)"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generator_module():
    """Load the selected generator from this exact repository/runtime tree."""
    module, _source, _sha256 = load_selected_generator(TASK_ID, root=find_root(__file__))
    return module


def canonical_program(root: str | Path) -> str:
    """Read the single canonical Racket program for this task."""
    matches = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}")
    program = matches[0].get("program_solution")
    if not isinstance(program, str):
        raise TypeError("canonical program_solution must be text")
    return program


def _validate_fill_color(value: int) -> int:
    if type(value) is not int:
        raise TypeError("fill_color must be a literal Python integer")
    if value not in ALLOWED_FILL_COLORS:
        raise ValueError(f"fill_color must be one of {ALLOWED_FILL_COLORS}")
    return value


def render_program(canonical: str, fill_color: int = DEFAULT_FILL_COLOR) -> str:
    """Return canonical bytes for 4 or one narrow fill-color substitution for 2."""
    fill_color = _validate_fill_color(fill_color)
    if not isinstance(canonical, str) or not canonical.startswith("(rule! ") or not canonical.endswith(")"):
        raise ValueError("canonical program must be a (rule! BODY) form")
    if canonical.count(_CANONICAL_CALL) != 1:
        raise ValueError("canonical fill-all-enclosed call was not found exactly once")
    if fill_color == DEFAULT_FILL_COLOR:
        return canonical
    return canonical.replace(
        _CANONICAL_CALL,
        f"(fill-all-enclosed g {fill_color})",
        1,
    )


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute exact instantiated Racket bytes with ``grid`` supplied as ``g``."""
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("expected a (rule! BODY) program")
    body = program[len("(rule! ") : -1]
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    bridge.define_grid("g", grid)
    output = bridge.eval_text(expression)
    if (
        not isinstance(output, list)
        or not output
        or not isinstance(output[0], list)
        or not output[0]
        or any(not isinstance(row, list) or len(row) != len(output[0]) for row in output)
        or any(type(value) is not int or not 0 <= value <= 9 for row in output for value in row)
    ):
        raise ValueError("Racket program did not return a nonempty rectangular ARC grid")
    return output


def fixture_inputs(seed: int) -> list[list[list[int]]]:
    """Return four distinct lawful inputs spanning small and canonical-scale scenes."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    generator = generator_module()
    profiles = (
        "single_10x10",
        "five_20x20",
        "double_10x10",
        "triple_10x10",
    )
    difficulties = ("easy", "medium", "hard", None)
    grids = []
    seen = set()
    for index, (profile, difficulty) in enumerate(zip(profiles, difficulties)):
        grid = generator.generate(
            seed ^ 0xAD5998AD,
            index,
            difficulty=difficulty,
            scene_profile=profile,
        )
        errors = generator.self_check(grid)
        if errors:
            raise ValueError(f"fixture left production domain: {errors}")
        if generator._analyze(grid)["enclosed_regions"] < 1:
            raise ValueError("fixture omitted the parameterized enclosed region")
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            raise ValueError("fixture inputs must be distinct")
        seen.add(key)
        grids.append(grid)
    return grids


def _build_episode(
    seed: int,
    fill_color: int,
    canonical: str,
    bridge: RacketBridge,
) -> dict[str, Any]:
    selected = _validate_fill_color(fill_color)
    rival = next(value for value in ALLOWED_FILL_COLORS if value != selected)
    programs = {value: render_program(canonical, value) for value in ALLOWED_FILL_COLORS}
    pairs = []
    rival_outputs = []
    for grid in fixture_inputs(seed):
        pairs.append({"input": grid, "output": execute(bridge, programs[selected], grid)})
        rival_outputs.append(execute(bridge, programs[rival], grid))

    demo_differences = [
        index
        for index, pair in enumerate(pairs[:3])
        if pair["output"] != rival_outputs[index]
    ]
    query_differs = pairs[3]["output"] != rival_outputs[3]
    if not demo_differences:
        raise ValueError("demonstrations do not distinguish the selected fill color")
    if query_differs and not demo_differences:
        raise ValueError("query needs a distinction absent from demonstrations")

    return {
        "schema": "ad5998ad11d6-parametric-fill-color-v1",
        "seed": seed,
        "parameters": {"fill_color": selected},
        "program": programs[selected],
        "program_sha256": _sha256_bytes(programs[selected].encode()),
        "train": pairs[:3],
        "test": pairs[3:],
        "rival": {
            "fill_color": rival,
            "program": programs[rival],
            "program_sha256": _sha256_bytes(programs[rival].encode()),
            "demo_differences": demo_differences,
            "query_differs": query_differs,
            "status": "distinguished" if demo_differences else "ambiguous",
            "outputs": {"train": rival_outputs[:3], "test": rival_outputs[3:]},
        },
        "label_authority": "included Racket bridge executing exact instantiated program text",
    }


def generate_episode(
    seed: int,
    *,
    fill_color: int | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Choose one rule setting and keep it fixed across 3 demos plus 1 query."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    selected = (
        random.Random(seed).choice(ALLOWED_FILL_COLORS)
        if fill_color is None
        else _validate_fill_color(fill_color)
    )
    root = find_root(__file__)
    canonical = canonical_program(root)
    if bridge is not None:
        return _build_episode(seed, selected, canonical, bridge)
    with RacketBridge() as owned_bridge:
        return _build_episode(seed, selected, canonical, owned_bridge)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Expose demos and query input while masking the setting, program, and answer."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def materialize(output: str | Path, *, seed: int = 73) -> dict[str, Any]:
    """Write a finite evidence gallery with exact Racket programs and source hashes."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    canonical = canonical_program(root)
    task_root = Path(__file__).resolve().parents[2]
    source_paths = [
        Path(__file__).resolve(),
        Path(__file__).with_name("README.md"),
        task_root / "generator.py",
        task_root / "tests" / "test_parametric_fill_color.py",
    ]
    source_hashes = {
        str(path.relative_to(root)): _sha256_bytes(path.read_bytes())
        for path in source_paths
        if path.is_file()
    }

    with RacketBridge(max_calls_before_restart=128) as bridge:
        episodes = [
            generate_episode(seed + index, fill_color=value, bridge=bridge)
            for index, value in enumerate(ALLOWED_FILL_COLORS)
        ]
        witness_input = fixture_inputs(seed)[0]
        witness_outputs = {
            str(value): execute(bridge, render_program(canonical, value), witness_input)
            for value in ALLOWED_FILL_COLORS
        }
        runtime_identity = bridge.runtime_identity

    for episode in episodes:
        value = episode["parameters"]["fill_color"]
        episode["prototype_source_sha256"] = source_hashes
        _write_json(output / "private" / f"episode-{value}.json", episode)
        _write_json(output / "public" / f"episode-{value}.json", public_challenge(episode))
        rules = output / "rules"
        rules.mkdir(parents=True, exist_ok=True)
        (rules / f"fill-color-{value}.rkt").write_text(episode["program"] + "\n")

    _write_json(
        output / "private" / "shared-input-witness.json",
        {
            "input": witness_input,
            "outputs": witness_outputs,
            "different": witness_outputs["4"] != witness_outputs["2"],
        },
    )
    report = {
        "schema": "ad5998ad11d6-parametric-fill-color-report-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameter": {"fill_color": list(ALLOWED_FILL_COLORS)},
        "default": DEFAULT_FILL_COLOR,
        "input_constraints_depending_on_parameter": [],
        "invariant_reasoning": [
            "identify black regions not 4-connected to any grid edge",
            "preserve every green wall and every edge-reachable black cell",
            "recolor every sealed black cell with the episode's one inferred fill color",
        ],
        "default_program_exact_canonical": episodes[0]["program"] == canonical,
        "complete_episodes": len(episodes),
        "pairs_per_episode": {"train": 3, "test": 1},
        "all_labels_and_rivals_executed_in_racket": True,
        "all_demonstrations_refute_other_setting": all(
            episode["rival"]["demo_differences"] == [0, 1, 2]
            for episode in episodes
        ),
        "all_queries_differ": all(episode["rival"]["query_differs"] for episode in episodes),
        "shared_input_outputs_differ": witness_outputs["4"] != witness_outputs["2"],
        "runtime_identity": runtime_identity,
        "source_sha256": source_hashes,
        "limitations": [
            "Only output colors 4 (canonical) and 2 (proposed) are compared.",
            "The parameter changes the recoloring value only; enclosure detection is unchanged.",
            "Evidence covers two retained episode seeds and four generated inputs per episode.",
            "The production generator and selected Racket authority remain fixed to color 4.",
            "Finite two-setting evidence is not proof of identifiability against every possible rival rule.",
        ],
    }
    _write_json(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=73)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = materialize(args.out, seed=args.seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "complete_episodes": report["complete_episodes"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
