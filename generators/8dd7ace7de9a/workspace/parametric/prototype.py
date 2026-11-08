"""Proposed output-extent parameter for periodic-tile recovery.

The hidden parameter is fixed once per episode:

* ``full_grid`` (canonical/default): recover the tile and repeat it over the
  original grid dimensions.
* ``tile_only`` (proposed): run the same recovery, then return one clean period
  tile instead of expanding it.

The prototype never changes the production generator or canonical authority.
Every retained label is executed by the materialized Racket program.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
TASK_ROOT = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
TASK_ID = "8dd7ace7de9a"

sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))
from reference_probe import canonical_program, load_generator  # noqa: E402
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402

PARAMETER = "output_extent"
VALUES = ("full_grid", "tile_only")
DEFAULT = "full_grid"

_BUILD_GRID_HEAD = "(build-grid hh\n                         ww"
_TILE_GRID_HEAD = "(build-grid tile-pr\n                         tile-pc"
_REPEAT_INDEX = "(list (remainder r tile-pr) (remainder c tile-pc))"
_TILE_INDEX = "(list r c)"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def materialize_programs() -> dict[str, str]:
    """Return exact canonical source plus the two-site output-extent variant."""
    canonical = canonical_program()
    if canonical.count(_BUILD_GRID_HEAD) != 1:
        raise ValueError("canonical program no longer has one expected output grid head")
    if canonical.count(_REPEAT_INDEX) != 1:
        raise ValueError("canonical program no longer has one expected repeat index")
    tile_only = canonical.replace(_BUILD_GRID_HEAD, _TILE_GRID_HEAD, 1)
    tile_only = tile_only.replace(_REPEAT_INDEX, _TILE_INDEX, 1)
    if tile_only == canonical:
        raise ValueError("tile-only materialization did not change the program")
    return {"full_grid": canonical, "tile_only": tile_only}


def choose_parameter(seed: int) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    digest = hashlib.sha256(f"{TASK_ID}|{PARAMETER}|{seed}".encode()).digest()
    return VALUES[digest[0] % len(VALUES)]


def _recipe(seed: int, index: int) -> dict[str, Any]:
    difficulties = ("easy", "medium", "hard", "medium")
    return {
        "seed": seed * 1009 + 97,
        "sample_index": (seed % 10_000) + index,
        "difficulty": difficulties[index % len(difficulties)],
    }


def _racket_outputs(
    grids: list[list[list[int]]], programs: dict[str, str]
) -> dict[str, list[list[list[int]]]]:
    """Execute both exact programs in the bundled real Racket runtime."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    names = list(VALUES)
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parametric-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO_ROOT), stage, TASK_ID)
        request = {
            "programs": [programs[name] for name in names],
            "grids": grids,
        }
        (stage / "request.json").write_text(json.dumps(request), encoding="utf-8")
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("request.json").read_text())
all_outputs = []
for program in request["programs"]:
    bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(program))
    try:
        all_outputs.append([
            runner._apply_rule(bridge, name, grid) for grid in request["grids"]
        ])
    finally:
        bridge.close()
print(json.dumps(all_outputs))
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=240)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        raw = json.loads(result["stdout"])
    if len(raw) != len(names) or any(len(outputs) != len(grids) for outputs in raw):
        raise RuntimeError("Racket worker returned an incomplete output batch")
    return dict(zip(names, raw, strict=True))


def build_episode(
    *,
    seed: int,
    parameter: str | None = None,
    n_train: int = 3,
    n_test: int = 4,
) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(n_train) is not int or type(n_test) is not int:
        raise TypeError("n_train and n_test must be integers")
    if n_train < 1 or n_test < 1:
        raise ValueError("n_train and n_test must be positive")
    selected = choose_parameter(seed) if parameter is None else parameter
    if selected not in VALUES:
        raise ValueError(f"parameter must be one of {VALUES}")

    generator = load_generator(TASK_ROOT / "generator.py")
    programs = materialize_programs()
    recipes = [_recipe(seed, index) for index in range(n_train + n_test)]
    grids = [generator.generate(**recipe) for recipe in recipes]
    grid_keys = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    if len(set(grid_keys)) != len(grid_keys):
        raise RuntimeError("episode sampler produced duplicate inputs")

    outputs_by_parameter = _racket_outputs(grids, programs)
    rival = next(value for value in VALUES if value != selected)
    pairs: list[dict[str, Any]] = []
    for index, (recipe, grid) in enumerate(zip(recipes, grids, strict=True)):
        by_parameter = {
            value: outputs_by_parameter[value][index] for value in VALUES
        }
        pairs.append(
            {
                "index": index,
                "recipe": recipe,
                "input": grid,
                "outputs_by_parameter": by_parameter,
                "selected_output": by_parameter[selected],
                "settings_disagree": by_parameter["full_grid"]
                != by_parameter["tile_only"],
            }
        )

    train = pairs[:n_train]
    test = pairs[n_train:]
    rival_fits_all_demos = all(
        pair["outputs_by_parameter"][rival] == pair["selected_output"]
        for pair in train
    )
    if rival_fits_all_demos:
        raise RuntimeError("demonstrations do not distinguish the alternate setting")

    public_challenge = {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["selected_output"]),
            }
            for pair in train
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in test],
    }
    public_id = public_challenge_id(public_challenge)
    return {
        "schema": f"{TASK_ID}-output-extent-parametric-v1",
        "seed": seed,
        "parameter_name": PARAMETER,
        "parameter": selected,
        "default": DEFAULT,
        "allowed_values": list(VALUES),
        "n_train": n_train,
        "n_test": n_test,
        "label_source": "real_racket",
        "programs": programs,
        "program_sha256": {
            value: _sha256_text(programs[value]) for value in VALUES
        },
        "pairs": pairs,
        "train": train,
        "test": test,
        "rival_parameter": rival,
        "rival_fits_all_demos": rival_fits_all_demos,
        "all_demos_distinguish": all(pair["settings_disagree"] for pair in train),
        "public_challenge": public_challenge,
        "public_id": public_id,
        "public_bytes_sha256": hashlib.sha256(
            public_challenge_bytes(public_challenge)
        ).hexdigest(),
        "limits": [
            "prototype only; production generate() remains bound to the canonical full-grid rule",
            "the setting is inferred from demonstrations and intentionally omitted from public files",
            "evidence is bounded to retained seeds and two output-extent values",
        ],
    }


def write_episode(episode: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir = Path(out_dir)
    public_dir = out_dir / "public"
    private_dir = out_dir / "private"
    summary_dir = out_dir / "summary"
    for directory in (public_dir, private_dir, summary_dir):
        directory.mkdir(parents=True, exist_ok=True)

    public_id = episode["public_id"]
    public_path = public_dir / f"{public_id}.json"
    private_path = private_dir / f"{public_id}.json"
    summary_path = summary_dir / f"{public_id}.json"
    existing = [path for path in (public_path, private_path, summary_path) if path.exists()]
    if existing:
        raise FileExistsError(
            f"duplicate public challenge {public_id}: {', '.join(str(path) for path in existing)}"
        )
    public_path.write_bytes(public_challenge_bytes(episode["public_challenge"]))
    private_path.write_text(json.dumps(episode, indent=2) + "\n", encoding="utf-8")
    summary = {
        "schema": episode["schema"],
        "public_id": public_id,
        "parameter_name": episode["parameter_name"],
        "parameter": episode["parameter"],
        "default": episode["default"],
        "n_train": episode["n_train"],
        "n_test": episode["n_test"],
        "label_source": episode["label_source"],
        "program_sha256": episode["program_sha256"],
        "all_demos_distinguish": episode["all_demos_distinguish"],
        "rival_fits_all_demos": episode["rival_fits_all_demos"],
        "pair_disagreements": [pair["settings_disagree"] for pair in episode["pairs"]],
        "artifacts": {
            "public": str(public_path.relative_to(out_dir)),
            "private": str(private_path.relative_to(out_dir)),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {
        "public": str(public_path),
        "private": str(private_path),
        "summary": str(summary_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--parameter", choices=VALUES)
    parser.add_argument("--n-train", type=int, default=3)
    parser.add_argument("--n-test", type=int, default=4)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    episode = build_episode(
        seed=args.seed,
        parameter=args.parameter,
        n_train=args.n_train,
        n_test=args.n_test,
    )
    paths = write_episode(episode, args.out_dir)
    print(
        json.dumps(
            {
                "public_id": episode["public_id"],
                "parameter": episode["parameter"],
                "n_train": episode["n_train"],
                "n_test": episode["n_test"],
                "label_source": episode["label_source"],
                "all_demos_distinguish": episode["all_demos_distinguish"],
                "rival_fits_all_demos": episode["rival_fits_all_demos"],
                "program_sha256": episode["program_sha256"],
                "paths": paths,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
