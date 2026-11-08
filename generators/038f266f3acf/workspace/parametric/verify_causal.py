"""Build and replay a qualification-bound beam-width causal witness.

The native qualification supplies exact protected-Racket episodes.  This tool
selects the largest query for each qualified setting, authors the intermediate
marker-derived depths, replaces only those depths with the reported cap-four
shortcut, and delegates construction plus replay to ``arcpuzzles.review_witness``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


_DESCRIPTIONS = {
    "step_a": (
        "For each red rim marker, grow the alternating row/column source box "
        "and measure the marker-to-opposite-edge source depth."
    ),
    "intermediate": (
        "The per-marker source depth, marker coordinate, source bounding box, "
        "launch edge, and outward direction derived from the unchanged input."
    ),
    "step_b": (
        "Extend the red center ray to the boundary and paint green side wings "
        "whose half-width is wing_multiplier times the derived source depth."
    ),
    "why_b_depends_on_a": (
        "Replacing only the marker-derived depths by min(depth, 4) preserves "
        "the input, setting, source objects, directions, red ray, and output "
        "shape but changes final green wing cells on every retained case."
    ),
}


def _load_prototype():
    source = Path(__file__).resolve().with_name("beam_width.py")
    if source.is_symlink() or not source.is_file():
        raise ImportError("verify_causal requires adjacent regular beam_width.py")
    body = source.read_bytes()
    name = "_beam_width_causal_" + hashlib.sha256(
        str(source).encode() + body
    ).hexdigest()
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load adjacent prototype: {source}")
    module = importlib.util.module_from_spec(spec)
    exec(compile(body, str(source), "exec"), module.__dict__)
    return module


_prototype = _load_prototype()


def _setting_key(settings):
    try:
        return json.dumps(
            settings,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValueError("qualification settings must be finite JSON") from error


def _qualified_episode(qualification, episode):
    if not isinstance(episode, dict):
        raise ValueError("qualification episode must be an object")
    settings = episode.get("settings")
    program = episode.get("program")
    key = _setting_key(settings)
    expected = qualification.get("programs", {}).get(key)
    if (
        not isinstance(program, str)
        or not program.strip()
        or not isinstance(expected, str)
        or hashlib.sha256(program.encode()).hexdigest() != expected
    ):
        raise ValueError("episode program is not the qualified program for its setting")
    multiplier = settings.get("wing_multiplier") if isinstance(settings, dict) else None
    if type(multiplier) is not int or multiplier not in _prototype.ALLOWED_MULTIPLIERS:
        raise ValueError("qualified setting needs wing_multiplier 1 or 2")
    return key, multiplier


def _largest_query(episode):
    pairs = episode.get("test")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("qualification episode needs query pairs")
    candidates = []
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            raise ValueError("qualification query pair needs input and output")
        grid = pair["input"]
        _prototype._grid(grid)
        _prototype._grid(pair["output"])
        candidates.append((len(grid) * len(grid[0]), len(grid), len(grid[0]), index, pair))
    return max(candidates, key=lambda row: row[:4])


def _intermediate(grid, multiplier):
    analysis = _prototype._analysis(grid)
    objects = []
    for rect in analysis["rectangles"]:
        objects.append(
            {
                "marker": list(rect["marker"]),
                "source_bbox": list(rect["bbox"]),
                "source_depth": rect["half_width"],
                "launch_edge": rect["edge"],
                "outward_direction": list(rect["direction"]),
            }
        )
    return {
        "grid_shape": [len(grid), len(grid[0])],
        "selected_wing_multiplier": multiplier,
        "source_depths": sorted(row["source_depth"] for row in objects),
        "objects": objects,
        "wrong_depth_cap": 4,
    }


def make_recipe(qualification, execution):
    """Return an authored recipe selecting one maximum-area query per setting."""
    if not isinstance(qualification, dict) or not isinstance(
        qualification.get("programs"), dict
    ):
        raise ValueError("qualification needs a setting-to-program map")
    episodes = execution.get("episodes") if isinstance(execution, dict) else None
    if not isinstance(episodes, list) or not episodes:
        raise ValueError("execution needs qualified episodes")

    selected = {}
    for episode_index, episode in enumerate(episodes):
        key, multiplier = _qualified_episode(qualification, episode)
        area, height, width, pair_index, pair = _largest_query(episode)
        candidate = (area, height, width, -episode_index, episode_index, pair_index, pair, multiplier)
        previous = selected.get(key)
        if previous is None or candidate[:4] > previous[:4]:
            selected[key] = candidate

    cases = []
    for key in sorted(selected):
        _, _, _, _, episode_index, pair_index, pair, multiplier = selected[key]
        counterfactual = _prototype.materialize_program(multiplier, cap_depth=4)
        if hashlib.sha256(counterfactual.encode()).hexdigest() == qualification["programs"][key]:
            raise ValueError("wrong-intermediate counterfactual must differ from qualified program")
        cases.append(
            {
                "episode_index": episode_index,
                "split": "test",
                "pair_index": pair_index,
                "counterfactual_program": counterfactual,
                "intermediate_value": _intermediate(pair["input"], multiplier),
                "ablation": "wrong_intermediate",
            }
        )
    if not 1 <= len(cases) <= 16:
        raise ValueError("causal recipe requires 1..16 setting cases")
    return {**_DESCRIPTIONS, "cases": cases}


def _find_root(start):
    for parent in (Path(start).resolve(), *Path(start).resolve().parents):
        if (parent / "shared" / "runtime").is_dir() and (parent / "generators").is_dir():
            return parent
    raise FileNotFoundError("Could not locate repository root")


def build(qualification_path, output, *, timeout=30.0):
    from arcpuzzles.review_witness import build_witness

    qualification_path = Path(qualification_path).resolve()
    qualification = json.loads(qualification_path.read_bytes())
    execution_path = qualification_path.with_name("execution.json")
    execution = json.loads(execution_path.read_bytes())
    recipe = make_recipe(qualification, execution)
    root = _find_root(Path(__file__).parent)
    result = build_witness(
        root, qualification_path, recipe, Path(output), timeout=timeout
    )
    recipe_path = Path(output) / "recipe.json"
    recipe_path.write_text(
        json.dumps(recipe, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    return {**result, "recipe_path": str(recipe_path.resolve())}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(argv)
    try:
        result = build(args.qualification, args.out, timeout=args.timeout)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(
        json.dumps(
            {
                "status": result["status"],
                "task_id": result["task_id"],
                "witness_path": result["witness_path"],
                "recipe_path": result["recipe_path"],
                "evaluations": result["construction"]["evaluations"],
                "training_admitted": result["training_admitted"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
