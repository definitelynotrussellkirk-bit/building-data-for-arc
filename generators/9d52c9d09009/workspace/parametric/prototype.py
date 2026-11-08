#!/usr/bin/env python3
"""Episode-level output-code parameter prototype for ARC task 9d52c9d09009.

This is intentionally separate from the fixed canonical production path.  It
chooses the color assigned to four bounding-box zero regions once per episode,
then executes the exact instantiated Racket program for every label and rival.
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


TASK_ID = "9d52c9d09009"
ALLOWED_FOUR_REGION_COLORS = (4, 7)
DEFAULT_FOUR_REGION_COLOR = 7
_CANONICAL_MAP = "(define (map-color n) (if (= n 4) 7 n))"
_ALTERNATIVE_MAP = "(define (map-color n) (if (= n 4) 4 n))"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generator_module():
    """Load the selected task source from this exact repository/runtime tree."""
    module, _source, _sha256 = load_selected_generator(TASK_ID, root=find_root(__file__))
    return module


def canonical_program(root: str | Path) -> str:
    matches = []
    with canonical_path(root).open() as handle:
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


def _validate_four_region_color(value: int) -> int:
    if type(value) is not int:
        raise TypeError("four_region_color must be a literal Python integer")
    if value not in ALLOWED_FOUR_REGION_COLORS:
        raise ValueError(f"four_region_color must be one of {ALLOWED_FOUR_REGION_COLORS}")
    return value


def render_program(canonical: str, four_region_color: int = DEFAULT_FOUR_REGION_COLOR) -> str:
    """Return exact canonical bytes for 7, or one narrow map-color substitution for 4."""
    four_region_color = _validate_four_region_color(four_region_color)
    if not isinstance(canonical, str) or not canonical.startswith("(rule! ") or not canonical.endswith(")"):
        raise ValueError("canonical program must be a (rule! BODY) form")
    if canonical.count(_CANONICAL_MAP) != 1:
        raise ValueError("canonical four-region map was not found exactly once")
    if four_region_color == DEFAULT_FOUR_REGION_COLOR:
        return canonical
    return canonical.replace(_CANONICAL_MAP, _ALTERNATIVE_MAP, 1)


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute exact instantiated Racket bytes with ``grid`` supplied as g."""
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
    """Four lawful all-count scenes; each contains both a 4-region object and a 4/8 witness."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    generator = generator_module()
    rng = random.Random(seed ^ 0x9D52C9D0)
    grids = []
    seen = set()
    for index in range(64):
        grid = generator.generate(
            rng.randrange(2**31),
            index,
            difficulty=("easy", "medium", "hard", None)[index % 4],
            scene_profile="all_counts",
        )
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            continue
        analysis = generator._analysis(grid)
        if analysis["errors"]:
            raise ValueError(f"fixture left production domain: {analysis['errors']}")
        if 4 not in analysis["facts"]["hole_signature"]:
            raise ValueError("fixture omitted the parameterized four-region object")
        if not generator._has_four_vs_eight_connectivity_witness(grid):
            raise ValueError("fixture omitted the production connectivity witness")
        seen.add(key)
        grids.append(grid)
        if len(grids) == 4:
            return grids
    raise RuntimeError("could not construct four distinct parametric fixtures")


def _build_episode(
    seed: int,
    four_region_color: int,
    canonical: str,
    bridge: RacketBridge,
) -> dict[str, Any]:
    selected = _validate_four_region_color(four_region_color)
    rival = next(value for value in ALLOWED_FOUR_REGION_COLORS if value != selected)
    programs = {value: render_program(canonical, value) for value in ALLOWED_FOUR_REGION_COLORS}
    pairs = []
    rival_outputs = []
    for grid in fixture_inputs(seed):
        pairs.append({"input": grid, "output": execute(bridge, programs[selected], grid)})
        rival_outputs.append(execute(bridge, programs[rival], grid))
    demo_differences = [
        index for index, pair in enumerate(pairs[:3]) if pair["output"] != rival_outputs[index]
    ]
    query_differs = pairs[3]["output"] != rival_outputs[3]
    if not demo_differences:
        raise ValueError("demonstrations do not distinguish the selected parameter")
    if query_differs and not demo_differences:
        raise ValueError("query needs a distinction absent from demonstrations")
    return {
        "schema": "9d52c9d09009-parametric-four-region-color-v1",
        "seed": seed,
        "parameters": {"four_region_color": selected},
        "program": programs[selected],
        "program_sha256": _sha256_bytes(programs[selected].encode()),
        "train": pairs[:3],
        "test": pairs[3:],
        "rival": {
            "four_region_color": rival,
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
    four_region_color: int | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Choose the rule parameter once and keep it fixed across 3 demos plus 1 query."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    selected = (
        random.Random(seed).choice(ALLOWED_FOUR_REGION_COLORS)
        if four_region_color is None
        else _validate_four_region_color(four_region_color)
    )
    root = find_root(__file__)
    canonical = canonical_program(root)
    if bridge is not None:
        return _build_episode(seed, selected, canonical, bridge)
    with RacketBridge() as owned_bridge:
        return _build_episode(seed, selected, canonical, owned_bridge)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Expose demonstrations and query input while masking rule setting and query answer."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def materialize(output: str | Path, *, seed: int = 73) -> dict[str, Any]:
    """Write a self-contained finite gallery with exact programs, labels, and hashes."""
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
        task_root / "tests" / "test_parametric_four_region_color.py",
    ]
    source_hashes = {
        str(path.relative_to(root)): _sha256_bytes(path.read_bytes())
        for path in source_paths
        if path.is_file()
    }

    with RacketBridge(max_calls_before_restart=128) as bridge:
        episodes = [
            generate_episode(seed + index, four_region_color=value, bridge=bridge)
            for index, value in enumerate((7, 4))
        ]
        witness_input = fixture_inputs(seed)[0]
        witness_outputs = {
            str(value): execute(bridge, render_program(canonical, value), witness_input)
            for value in ALLOWED_FOUR_REGION_COLORS
        }
        runtime_identity = bridge.runtime_identity

    for episode in episodes:
        value = episode["parameters"]["four_region_color"]
        episode["prototype_source_sha256"] = source_hashes
        _write_json(output / "private" / f"episode-{value}.json", episode)
        _write_json(output / "public" / f"episode-{value}.json", public_challenge(episode))
        (output / "rules").mkdir(parents=True, exist_ok=True)
        (output / "rules" / f"four-region-color-{value}.rkt").write_text(episode["program"])

    _write_json(
        output / "private" / "shared-input-witness.json",
        {
            "input": witness_input,
            "outputs": witness_outputs,
            "different": witness_outputs["4"] != witness_outputs["7"],
        },
    )
    report = {
        "schema": "9d52c9d09009-parametric-four-region-color-report-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameter": {"four_region_color": list(ALLOWED_FOUR_REGION_COLORS)},
        "default": DEFAULT_FOUR_REGION_COLOR,
        "default_program_exact_canonical": episodes[0]["program"] == canonical,
        "complete_episodes": len(episodes),
        "pairs_per_episode": {"train": 3, "test": 1},
        "all_labels_and_rivals_executed_in_racket": True,
        "all_demonstrations_refute_other_setting": all(
            episode["rival"]["demo_differences"] == [0, 1, 2] for episode in episodes
        ),
        "all_queries_differ": all(episode["rival"]["query_differs"] for episode in episodes),
        "shared_input_outputs_differ": witness_outputs["4"] != witness_outputs["7"],
        "runtime_identity": runtime_identity,
        "source_sha256": source_hashes,
        "limitations": [
            "Only output colors 7 (canonical) and 4 (proposed) are compared.",
            "The parameter changes only the four-region mapping; object detection and region counting are unchanged.",
            "Evidence covers two retained episode seeds and four generated all-count inputs per episode.",
            "The production generator remains fixed to the canonical color 7; this prototype has no approval or export status.",
            "Finite declared-setting evidence is not proof of identifiability against every possible rival rule.",
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
    print(json.dumps({
        "status": report["status"],
        "complete_episodes": report["complete_episodes"],
        "out": str(args.out),
    }))


if __name__ == "__main__":
    main()
