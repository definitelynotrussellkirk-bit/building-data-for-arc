"""Isolated Racket-backed scale-factor episodes for ``2dacb90452ce``.

This prototype does not alter the production generator or canonical authority.
The episode-wide ``scale_factor`` is either the canonical value 2 or the nearby
variant 3.  Every retained label and counterfactual is executed through Racket.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "2dacb90452ce"
SCALE_FACTORS = (2, 3)
DEFAULT_SCALE_FACTOR = 2
DEFAULT_DEMO_COUNT = 2
DEFAULT_QUERY_COUNT = 4


def sha256(value: str | bytes) -> str:
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_seed(seed) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative Python int (not bool)")
    return seed


def validate_scale_factor(scale_factor) -> int:
    """Validate one exact episode-wide scale factor."""
    if type(scale_factor) is not int or scale_factor not in SCALE_FACTORS:
        raise ValueError(
            f"scale_factor must be one of {SCALE_FACTORS}, as a Python int (not bool)"
        )
    return scale_factor


def validate_pair_counts(demo_count, query_count) -> tuple[int, int]:
    """Validate separately exposed positive demonstration and query counts."""
    if type(demo_count) is not int or demo_count < 1:
        raise ValueError("demo_count must be a positive Python int (not bool)")
    if type(query_count) is not int or query_count < 1:
        raise ValueError("query_count must be a positive Python int (not bool)")
    return demo_count, query_count


@lru_cache(maxsize=4)
def canonical_rule(*, root=None) -> str:
    """Return the one unique exact canonical Racket program for this task."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            source = row.get("program_solution")
            if not isinstance(source, str) or not source:
                raise ValueError("Canonical row is missing an exact program_solution.")
            sources.append(source)
    unique = set(sources)
    if not sources or len(unique) != 1:
        raise ValueError(
            "The scale-factor prototype requires one unique exact canonical rule; "
            f"found {len(sources)} rows and {len(unique)} unique sources."
        )
    return sources[0]


def program_for_scale_factor(scale_factor=DEFAULT_SCALE_FACTOR, *, root=None) -> str:
    """Materialize the exact Racket authority for one scale factor.

    Factor 2 is returned byte-for-byte from the canonical ledger.  Factor 3
    changes only the integer argument of the selected ``upscale`` call.
    """
    scale_factor = validate_scale_factor(scale_factor)
    source = canonical_rule(root=root)
    if scale_factor == DEFAULT_SCALE_FACTOR:
        return source
    site = "(upscale g 2)"
    if source.count(site) != 1:
        raise ValueError(
            "Canonical upscale call changed; reassess the scale-factor prototype."
        )
    return source.replace(site, f"(upscale g {scale_factor})", 1)


def evaluate(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute one exact program on one normalized grid through Racket."""
    normalized = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("Expected the selected task's native Racket lambda.")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def choose_scale_factor(seed) -> int:
    """Choose one factor once per episode without touching global RNG state."""
    seed = _validate_seed(seed)
    return SCALE_FACTORS[seed % len(SCALE_FACTORS)]


def _grid_key(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def generate_inputs(
    seed,
    *,
    demo_count=DEFAULT_DEMO_COUNT,
    query_count=DEFAULT_QUERY_COUNT,
    root=None,
) -> list[list[list[int]]]:
    """Draw distinct, setting-independent inputs from the selected generator."""
    seed = _validate_seed(seed)
    demo_count, query_count = validate_pair_counts(demo_count, query_count)
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    total = demo_count + query_count
    inputs: list[list[list[int]]] = []
    seen: set[tuple[tuple[int, ...], ...]] = set()
    bands = ("easy", "medium", "hard")

    # Explicit sizes make a six-pair episode span the canonical scale.  Seeds,
    # sample indices and difficulties vary deterministically, never by setting.
    for attempt in range(max(64, total * 16)):
        size = 2 + (attempt % 4)
        sample_index = seed * 17 + attempt
        draw_seed = seed * 1_000_003 + attempt * 97 + 23
        grid = generator.generate(
            draw_seed,
            sample_index,
            difficulty=bands[attempt % len(bands)],
            grid_size=size,
        )
        key = _grid_key(grid)
        if key in seen:
            continue
        if generator.self_check(grid):
            continue
        if len(grid) * max(SCALE_FACTORS) > 30 or len(grid[0]) * max(SCALE_FACTORS) > 30:
            continue
        seen.add(key)
        inputs.append([list(row) for row in grid])
        if len(inputs) == total:
            return inputs
    raise RuntimeError(f"could not construct {total} distinct lawful inputs")


def generate_episode(
    bridge: RacketBridge,
    seed,
    *,
    scale_factor=None,
    demo_count=DEFAULT_DEMO_COUNT,
    query_count=DEFAULT_QUERY_COUNT,
    root=None,
) -> dict:
    """Choose one factor once and label all pairs with its exact Racket program."""
    seed = _validate_seed(seed)
    demo_count, query_count = validate_pair_counts(demo_count, query_count)
    root = find_root(__file__) if root is None else Path(root).resolve()
    chosen = (
        choose_scale_factor(seed)
        if scale_factor is None
        else validate_scale_factor(scale_factor)
    )
    program = program_for_scale_factor(chosen, root=root)
    pairs = [
        {"input": grid, "output": evaluate(bridge, program, grid)}
        for grid in generate_inputs(
            seed,
            demo_count=demo_count,
            query_count=query_count,
            root=root,
        )
    ]
    return {
        "schema": "arcpuzzles-parametric-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {"scale_factor": chosen},
        "parameter_choice": (
            "seed_modulo_two" if scale_factor is None else "explicit_once_per_episode"
        ),
        "counts": {"demonstrations": demo_count, "queries": query_count},
        "racket_program": program,
        "racket_sha256": sha256(program),
        "pairs": pairs,
    }


def analyze_episode(bridge: RacketBridge, episode: dict, *, root=None) -> dict:
    """Check every query against the sole alternative factor using demos only."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    chosen = validate_scale_factor(episode["parameters"]["scale_factor"])
    demo_count, query_count = validate_pair_counts(
        episode["counts"]["demonstrations"], episode["counts"]["queries"]
    )
    pairs = episode["pairs"]
    if len(pairs) != demo_count + query_count:
        raise ValueError("episode pair count disagrees with declared counts")
    rival = next(value for value in SCALE_FACTORS if value != chosen)
    rival_program = program_for_scale_factor(rival, root=root)
    rival_outputs = [
        evaluate(bridge, rival_program, pair["input"])
        for pair in pairs
    ]
    refuting_demo_indices = [
        index
        for index in range(demo_count)
        if rival_outputs[index] != pairs[index]["output"]
    ]
    rival_fits = not refuting_demo_indices
    pair_checks = [
        {
            "pair_index": index,
            "role": "demonstration" if index < demo_count else "query",
            "chosen_output_sha256": sha256(
                json.dumps(pair["output"], separators=(",", ":"))
            ),
            "rival_output_sha256": sha256(
                json.dumps(rival_outputs[index], separators=(",", ":"))
            ),
            "differs": rival_outputs[index] != pair["output"],
        }
        for index, pair in enumerate(pairs)
    ]
    queries = []
    for query_offset in range(query_count):
        pair_index = demo_count + query_offset
        queries.append(
            {
                "query_index": query_offset,
                "pair_index": pair_index,
                "rival_scale_factor": rival,
                "rival_fits_demonstrations": rival_fits,
                "query_differs": rival_outputs[pair_index] != pairs[pair_index]["output"],
                "refuting_demonstration_indices": refuting_demo_indices,
            }
        )
    status = (
        "no_ambiguity_found"
        if all((not row["rival_fits_demonstrations"]) and row["query_differs"] for row in queries)
        else "ambiguity_found"
    )
    return {
        "status": status,
        "chosen_scale_factor": chosen,
        "rival_scale_factor": rival,
        "rival_racket_sha256": sha256(rival_program),
        "pair_checks": pair_checks,
        "queries": queries,
    }


def public_challenge(episode: dict) -> dict:
    """Return only visible demonstrations and unlabeled query inputs."""
    demo_count, query_count = validate_pair_counts(
        episode["counts"]["demonstrations"], episode["counts"]["queries"]
    )
    pairs = episode["pairs"]
    if len(pairs) != demo_count + query_count:
        raise ValueError("episode pair count disagrees with declared counts")
    challenge = {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in pairs[:demo_count]
        ],
        "test": [
            {"input": pair["input"]}
            for pair in pairs[demo_count:]
        ],
    }
    # Normalize through the shared helper now, not only when writing.
    public_challenge_bytes(challenge)
    return deepcopy(challenge)


def public_filename(episode: dict) -> str:
    return f"challenge-{public_challenge_id(public_challenge(episode))}.json"


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_evidence(
    out,
    *,
    seed,
    demo_count=DEFAULT_DEMO_COUNT,
    query_count=DEFAULT_QUERY_COUNT,
    bridge=None,
    root=None,
) -> dict:
    """Build immutable public/private evidence for both parameter settings."""
    seed = _validate_seed(seed)
    demo_count, query_count = validate_pair_counts(demo_count, query_count)
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence directory: {out}")
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    del generator
    out.mkdir(parents=True)
    (out / "public").mkdir()
    (out / "private" / "episodes").mkdir(parents=True)
    (out / "private" / "rules").mkdir(parents=True)

    programs = {
        factor: program_for_scale_factor(factor, root=root)
        for factor in SCALE_FACTORS
    }
    for factor, program in programs.items():
        (out / "private" / "rules" / f"scale-factor-{factor}.rkt").write_text(
            program, encoding="utf-8"
        )

    context = nullcontext(bridge) if bridge is not None else RacketBridge()
    with context as active:
        canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
        canonical_passed = sum(
            evaluate(active, programs[DEFAULT_SCALE_FACTOR], pair["input"])
            == pair["output"]
            for pair in canonical
        )
        if canonical_passed != len(canonical):
            raise RuntimeError("default scale factor did not reproduce every canonical label")

        episodes = []
        ambiguous_queries = 0
        counterfactual_labels = 0
        public_ids: set[str] = set()
        built_episodes = []
        for episode_index in range(len(SCALE_FACTORS)):
            episode_seed = seed + episode_index
            episode = generate_episode(
                active,
                episode_seed,
                demo_count=demo_count,
                query_count=query_count,
                root=root,
            )
            analysis = analyze_episode(active, episode, root=root)
            built_episodes.append(episode)
            counterfactual_labels += len(analysis["pair_checks"])
            ambiguous_queries += sum(
                row["rival_fits_demonstrations"] or not row["query_differs"]
                for row in analysis["queries"]
            )
            public = public_challenge(episode)
            public_id = public_challenge_id(public)
            if public_id in public_ids:
                raise RuntimeError("duplicate visible public challenge")
            public_ids.add(public_id)
            public_rel = Path("public") / f"challenge-{public_id}.json"
            private_rel = Path("private") / "episodes" / f"episode-{episode_index:03d}.json"
            (out / public_rel).write_bytes(public_challenge_bytes(public))
            private_episode = deepcopy(episode)
            private_episode["analysis"] = analysis
            _write_json(out / private_rel, private_episode)
            episodes.append(
                {
                    "episode_index": episode_index,
                    "seed": episode_seed,
                    "parameters": episode["parameters"],
                    "racket_sha256": episode["racket_sha256"],
                    "public_id": public_id,
                    "public_path": public_rel.as_posix(),
                    "private_path": private_rel.as_posix(),
                    "analysis": analysis,
                }
            )

        if {row["parameters"]["scale_factor"] for row in episodes} != set(SCALE_FACTORS):
            raise RuntimeError("two consecutive episode seeds did not cover both settings")

        witness_input = built_episodes[0]["pairs"][0]["input"]
        witness_outputs = {
            str(factor): evaluate(active, program, witness_input)
            for factor, program in programs.items()
        }

    prototype_path = Path(__file__).resolve()
    test_path = root / "generators" / TASK_ID / "tests" / "test_parametric_scale_factor.py"
    report = {
        "schema": "arcpuzzles-parametric-evidence-v1",
        "task_id": TASK_ID,
        "status": "no_ambiguity_found" if ambiguous_queries == 0 else "ambiguity_found",
        "prototype_status": "proposed",
        "parameters": {
            "name": "scale_factor",
            "allowed_values": list(SCALE_FACTORS),
            "default": DEFAULT_SCALE_FACTOR,
        },
        "input_constraints": {
            "source": "selected production generator",
            "side_lengths": [2, 3, 4, 5],
            "maximum_output_side_at_factor_3": 15,
        },
        "requested_counts": {
            "demonstrations_per_episode": demo_count,
            "queries_per_episode": query_count,
        },
        "counts": {
            "canonical_labels_checked": len(canonical),
            "canonical_labels_passed": canonical_passed,
            "episodes": len(episodes),
            "demonstrations": len(episodes) * demo_count,
            "queries": len(episodes) * query_count,
            "episode_labels": len(episodes) * (demo_count + query_count),
            "counterfactual_labels": counterfactual_labels,
            "ambiguous_queries": ambiguous_queries,
        },
        "sources": {
            "prototype_path": prototype_path.relative_to(root).as_posix(),
            "prototype_sha256": sha256(prototype_path.read_bytes()),
            "test_path": test_path.relative_to(root).as_posix(),
            "test_sha256": sha256(test_path.read_bytes()),
            "production_generator_path": generator_path.relative_to(root).as_posix(),
            "production_generator_sha256": generator_sha,
            "canonical_rule_sha256": sha256(programs[DEFAULT_SCALE_FACTOR]),
        },
        "rules": {
            str(factor): {
                "path": f"private/rules/scale-factor-{factor}.rkt",
                "sha256": sha256(program),
                "text": program,
            }
            for factor, program in programs.items()
        },
        "episodes": episodes,
        "setting_witness": {
            "input": witness_input,
            "outputs": witness_outputs,
        },
        "limits": [
            "Only scale factors 2 and 3 are assessed.",
            "Identifiability is checked against the sole declared alternative factor.",
            "Evidence covers two deterministic episodes, not every seed or input ordering.",
            "The prototype is separate from production approval and training admission.",
        ],
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--demo-count", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_evidence(
        args.out,
        seed=args.seed,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
