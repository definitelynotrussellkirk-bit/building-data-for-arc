"""Bounded source-local audit for the midpoint cue-gap family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root

TASK_ID = "02fcd49e49d6"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parent
SETTING_KEY = "selection"
SETTINGS = ("all_pairs", "cue_gap")
MIN_DEMOS = 2
CENSUS_SEEDS = 5_000


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _raw(value) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [
        pair["input"]
        for split in ("train", "test")
        for pair in episode[split]
    ]


def _catalogs(prototype, episode: dict) -> tuple[tuple[str, ...], list[dict]]:
    catalogs = [prototype.rival_outputs(pair["input"]) for pair in episode["train"]]
    names = tuple(catalogs[0])
    if any(tuple(catalog) != names for catalog in catalogs[1:]):
        raise AssertionError("rival catalog changed across demonstrations")
    return names, catalogs


def _survivors(names: tuple[str, ...], catalogs: list[dict], episode: dict) -> list[str]:
    return [
        name
        for name in names
        if all(
            catalog[name] == pair["output"]
            for catalog, pair in zip(catalogs, episode["train"])
        )
    ]


def _adversarial_census(prototype, seed_count: int) -> dict:
    """Scan minimum-demo lessons over many seeds without emitting bulky episodes."""
    if type(seed_count) is not int or seed_count < 1:
        raise ValueError("seed_count must be a positive exact integer")

    digest = hashlib.sha256()
    unexpected = []
    catalog_names: tuple[str, ...] | None = None
    case_count = 0
    for seed in range(seed_count):
        episodes = {
            setting: prototype.generate(
                seed, {SETTING_KEY: setting}, MIN_DEMOS, 1
            )
            for setting in SETTINGS
        }
        reference_inputs = _inputs(episodes[SETTINGS[0]])
        if any(_inputs(episodes[setting]) != reference_inputs for setting in SETTINGS[1:]):
            raise AssertionError(f"settings changed sampled inputs at seed {seed}")

        names, catalogs = _catalogs(prototype, episodes[SETTINGS[0]])
        if catalog_names is None:
            catalog_names = names
        elif names != catalog_names:
            raise AssertionError(f"rival catalog changed at seed {seed}")

        input_sha256 = hashlib.sha256(_raw(reference_inputs)).hexdigest()
        for setting in SETTINGS:
            survivors = _survivors(names, catalogs, episodes[setting])
            case_count += 1
            digest.update(_raw({
                "seed": seed,
                "setting": setting,
                "survivors": survivors,
                "input_sha256": input_sha256,
            }))
            if survivors != [setting] and len(unexpected) < 32:
                unexpected.append({
                    "seed": seed,
                    "setting": setting,
                    "survivors": survivors,
                    "input_sha256": input_sha256,
                })

    assert catalog_names is not None
    return {
        "status": "passed" if not unexpected else "failed",
        "seed_count": seed_count,
        "case_count": case_count,
        "minimum_demos": MIN_DEMOS,
        "queries_per_case": 1,
        "settings": list(SETTINGS),
        "rival_count": len(catalog_names),
        "rivals": list(catalog_names),
        "shortcut_evaluations": (
            seed_count * len(SETTINGS) * MIN_DEMOS * len(catalog_names)
        ),
        "unexpected_survivors": unexpected,
        "census_sha256": digest.hexdigest(),
    }


def run() -> dict:
    prototype = _load("_probe_midpoint_cue", HOME / "prototype.py")
    contract = json.loads((HOME / "promotion.json").read_text())
    settings_rows = [{SETTING_KEY: setting} for setting in SETTINGS]
    python_cases = []
    for seed in (0, 17):
        for demos in range(MIN_DEMOS, 7):
            episodes = {
                setting: prototype.generate(seed, {SETTING_KEY: setting}, demos, 4)
                for setting in SETTINGS
            }
            inputs = {name: _inputs(episode) for name, episode in episodes.items()}
            if inputs[SETTINGS[0]] != inputs[SETTINGS[1]]:
                raise AssertionError("settings changed sampled inputs")
            prefix = prototype.generate(seed, {SETTING_KEY: "cue_gap"}, demos, 1)
            if (
                prefix["train"] != episodes["cue_gap"]["train"]
                or prefix["test"] != episodes["cue_gap"]["test"][:1]
            ):
                raise AssertionError("one-query prefix changed visible episode content")

            names, catalogs = _catalogs(prototype, episodes[SETTINGS[0]])
            for name, episode in episodes.items():
                serialized = [json.dumps(grid, separators=(",", ":")) for grid in inputs[name]]
                if len(serialized) != len(set(serialized)):
                    raise AssertionError("episode contains duplicate inputs")
                survivors = _survivors(names, catalogs, episode)
                if survivors != [name]:
                    raise AssertionError(
                        f"unexpected demo-only survivors for {name}: {survivors}"
                    )
                python_cases.append({
                    "seed": seed,
                    "demos": demos,
                    "queries": 4,
                    SETTING_KEY: name,
                    "survivors": survivors,
                    "rival_count": len(names),
                    "input_sha256": hashlib.sha256(_raw(inputs[name])).hexdigest(),
                    "largest_query": [
                        len(episode["test"][-1]["input"]),
                        len(episode["test"][-1]["input"][0]),
                    ],
                })

    census = _adversarial_census(prototype, CENSUS_SEEDS)
    if census["status"] != "passed":
        raise AssertionError(f"adversarial census failed: {census['unexpected_survivors']}")

    jobs = [
        {"seed": seed, "settings": setting, "demos": MIN_DEMOS, "queries": 4}
        for setting in settings_rows
        for seed in (0, 17)
    ]
    native = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    compact_native = {
        "racket": native["racket"],
        "racket_evaluations": native["racket_evaluations"],
        "checks": native["checks"],
        "episode_sha256": [
            hashlib.sha256(_raw(row)).hexdigest() for row in native["episodes"]
        ],
    }
    sources = {}
    for path in sorted(HOME.iterdir()):
        if path.is_file() and path.suffix in {".py", ".rkt", ".json"}:
            sources[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "schema": "arcpuzzles-midpoint-cue-gap-probe-v2",
        "status": "passed",
        "task_id": TASK_ID,
        "scope": (
            "two settings; seeds 0 and 17 across demo counts 2..6 and four "
            "queries; 5,000-seed minimum-demo adversarial census over 25 named "
            "rivals; four protected-Racket native jobs"
        ),
        "sources": sources,
        "python_cases": python_cases,
        "adversarial_census": census,
        "native": compact_native,
        "limits": (
            "Finite seeds and named rivals; this does not prove uniqueness or "
            "owner acceptance."
        ),
    }


def main() -> int:
    report = run()
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
