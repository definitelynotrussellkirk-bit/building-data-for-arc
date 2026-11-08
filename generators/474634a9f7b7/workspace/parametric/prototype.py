#!/usr/bin/env python3
"""Bounded episode-level bar-length prototype for ARC task 474634a9f7b7.

This authoring prototype is intentionally separate from the selected production
rule.  It chooses one bar length per episode, executes the corresponding exact
Racket rule for every label and parameter rival, and retains public challenges
without query answers or hidden parameter values.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shlex
import subprocess
import sys
import traceback
import types
from typing import Any

from arc_repl import racket_bridge
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
import reviewer_support
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "474634a9f7b7"
PROTOTYPE_VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
CANONICAL_SHA256 = "83ceda10e2640019876233056742b15561dc5eb3c0ac060414945e9288d236d3"
BAR_LENGTHS = (1, 3)
DEFAULT_BAR_LENGTH = 3
_TEMPLATE = "(list -1 0 1)"
_REPLACEMENT = "(list 0)"
_TEMPLATE_OCCURRENCES = 4


def _load_main_generator():
    source = HERE.parent.parent / "generator.py"
    spec = importlib.util.spec_from_file_location(
        "parametric_474634a9f7b7_main_generator", source
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load selected generator from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MAIN = _load_main_generator()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def value_hash(value: Any) -> str:
    return sha256_bytes(json_bytes(value))


def _integer(value: Any, name: str, *, minimum: int | None = None) -> int:
    if type(value) is not int or (minimum is not None and value < minimum):
        suffix = f" >= {minimum}" if minimum is not None else ""
        raise ValueError(f"{name} must be an integer{suffix}")
    return value


@dataclass(frozen=True)
class Parameters:
    """The canonical/default setting paints the original three-cell bar."""

    bar_length: int = DEFAULT_BAR_LENGTH

    def __post_init__(self) -> None:
        if type(self.bar_length) is not int or self.bar_length not in BAR_LENGTHS:
            raise ValueError(
                f"bar_length must be one of {BAR_LENGTHS}; booleans and coercible scalars are invalid"
            )

    @property
    def key(self) -> str:
        return f"bar-length-{self.bar_length}"


def all_parameters() -> tuple[Parameters, ...]:
    return tuple(Parameters(length) for length in BAR_LENGTHS)


def _rng(seed: int, label: str) -> random.Random:
    _integer(seed, "seed")
    digest = hashlib.sha256(
        f"{TASK_ID}:parametric-bar-length-v1:{seed}:{label}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def sample_parameters(seed: int) -> Parameters:
    """Choose the rule setting once; input draws use disjoint streams."""
    return Parameters(_rng(seed, "parameter:bar_length").choice(BAR_LENGTHS))


def canonical_program() -> str:
    source = (HERE / "canonical_rule.rkt").read_text(encoding="utf-8")
    if sha256_bytes(source.encode()) != CANONICAL_SHA256:
        raise ValueError("the exact canonical Racket snapshot changed")
    if source.count(_TEMPLATE) != _TEMPLATE_OCCURRENCES:
        raise ValueError("the bounded bar template no longer matches canonical source")
    return source


def materialize_program(parameters: Parameters = Parameters()) -> str:
    """Return exact executable Racket; the default is byte-identical canonical."""
    if not isinstance(parameters, Parameters):
        raise TypeError("parameters must be a Parameters instance")
    source = canonical_program()
    if parameters.bar_length == DEFAULT_BAR_LENGTH:
        return source
    changed = source.replace(_TEMPLATE, _REPLACEMENT)
    if changed.count(_REPLACEMENT) != _TEMPLATE_OCCURRENCES or _TEMPLATE in changed:
        raise ValueError("failed to materialize all four orientation branches")
    return changed


def sample_input(seed: int, pair_index: int) -> list[list[int]]:
    """Draw lawful inputs from the selected family, independently of the rule setting."""
    _integer(seed, "seed")
    _integer(pair_index, "pair_index", minimum=0)
    input_seed = _rng(seed, f"input:{pair_index}").randrange(2**63)
    return MAIN.generate(input_seed, pair_index, difficulty="medium")


def witness_input() -> list[list[int]]:
    return MAIN.generate(
        20261019,
        2,
        difficulty="hard",
        grid_h=20,
        grid_w=20,
        target_side="bottom",
        target_size=22,
        shape_family="branched",
    )


def _grid(value: Any) -> list[list[int]]:
    if not isinstance(value, list) or not value:
        raise ValueError("Racket inputs and outputs must be nonempty grids")
    if any(not isinstance(row, list) or not row for row in value):
        raise ValueError("Racket grid rows must be nonempty lists")
    if len({len(row) for row in value}) != 1:
        raise ValueError("Racket grids must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row):
        raise ValueError("Racket grids require exact integer ARC colors 0..9")
    return value


def _grid_literal(grid: list[list[int]]) -> str:
    _grid(grid)
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def _install_scripts_namespace() -> None:
    root = find_root(__file__)
    tools = root / "shared" / "tools"
    if "scripts" not in sys.modules and tools.is_dir():
        package = types.ModuleType("scripts")
        package.__path__ = [str(tools)]
        sys.modules["scripts"] = package


def rule_application(source: str, grid: list[list[int]]) -> str:
    allowed = {materialize_program(parameters) for parameters in all_parameters()}
    if source not in allowed:
        raise ValueError("only the two pinned bar-length templates can be applied")
    _install_scripts_namespace()
    from puzzle_generators.rule_wrap import wrap_rule

    return f"({wrap_rule(source)} {_grid_literal(grid)})"


class RacketOracle:
    """Reusable Racket bridge with content-addressed execution evidence."""

    def __init__(self) -> None:
        self.root = find_root(__file__)
        for module in (racket_bridge, reviewer_support):
            if not Path(module.__file__).resolve().is_relative_to(self.root):
                raise ImportError(f"{module.__name__} belongs to another checkout")
        self.bridge = RacketBridge(timeout=10.0, max_calls_before_restart=128)
        self.executions: list[dict[str, Any]] = []
        self.cache: dict[tuple[str, str], list[list[int]]] = {}
        self.cache_hits = 0

    def evaluate(self, parameters: Parameters, grid: list[list[int]]) -> list[list[int]]:
        _grid(grid)
        source = materialize_program(parameters)
        source_hash = sha256_bytes(source.encode())
        input_hash = value_hash(grid)
        key = source_hash, input_hash
        if key in self.cache:
            self.cache_hits += 1
            return copy.deepcopy(self.cache[key])
        expression = rule_application(source, grid)
        output = _grid(self.bridge.eval_text(expression))
        if (len(output), len(output[0])) != (len(grid), len(grid[0])):
            raise ValueError("the executed rule changed grid dimensions")
        row = {
            "execution_index": len(self.executions),
            "backend": "RacketBridge.eval_text",
            "parameters": asdict(parameters),
            "program_sha256": source_hash,
            "input": copy.deepcopy(grid),
            "input_sha256": input_hash,
            "output": copy.deepcopy(output),
            "output_sha256": value_hash(output),
            "expression_sha256": sha256_bytes(expression.encode()),
        }
        self.executions.append(row)
        self.cache[key] = copy.deepcopy(output)
        return copy.deepcopy(output)

    def close(self) -> None:
        self.bridge.shutdown()


def rival_status(differing_train: list[int], differing_test: list[int]) -> str:
    if differing_train:
        return "refuted_by_demonstrations"
    return "ambiguous" if differing_test else "survived_all"


def build_episode(
    seed: int,
    parameters: Parameters = Parameters(),
    *,
    oracle: RacketOracle,
    n_train: int = 4,
    n_test: int = 1,
    parameter_selection: str = "fixed/default",
) -> dict[str, Any]:
    """Fix one setting, then execute every demo, query, and parameter rival."""
    _integer(seed, "seed")
    _integer(n_train, "n_train", minimum=1)
    _integer(n_test, "n_test", minimum=1)
    if n_train > 8 or n_test > 4:
        raise ValueError("bounded prototype permits at most 8 demos and 4 queries")
    if not isinstance(parameters, Parameters):
        raise TypeError("parameters must be a Parameters instance")

    inputs = [sample_input(seed, index) for index in range(n_train + n_test)]
    predictions = {
        setting.key: [oracle.evaluate(setting, grid) for grid in inputs]
        for setting in all_parameters()
    }
    selected = predictions[parameters.key]
    pairs = [
        {"input": copy.deepcopy(grid), "output": copy.deepcopy(output)}
        for grid, output in zip(inputs, selected)
    ]
    rivals = []
    for rival in all_parameters():
        if rival == parameters:
            continue
        prediction = predictions[rival.key]
        train_diff = [index for index in range(n_train) if prediction[index] != selected[index]]
        test_diff = [
            index
            for index in range(n_test)
            if prediction[n_train + index] != selected[n_train + index]
        ]
        rivals.append(
            {
                "parameters": asdict(rival),
                "program_sha256": sha256_bytes(materialize_program(rival).encode()),
                "status": rival_status(train_diff, test_diff),
                "differing_train_indices": train_diff,
                "differing_test_indices": test_diff,
                "predictions": {
                    "train": prediction[:n_train],
                    "test": prediction[n_train:],
                },
            }
        )
    if any(row["status"] != "refuted_by_demonstrations" for row in rivals):
        raise ValueError("the episode does not refute every bar-length rival in demonstrations")

    public = {
        "train": copy.deepcopy(pairs[:n_train]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in pairs[n_train:]],
    }
    source = materialize_program(parameters)
    return {
        "schema": "474634a9f7b7-parametric-bar-length-episode-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": asdict(parameters),
        "parameter_selection": parameter_selection,
        "parameters_fixed_for_all_pairs": True,
        "program": source,
        "program_sha256": sha256_bytes(source.encode()),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "public": public,
        "public_sha256": value_hash(public),
        "input_draws": [
            {"pair_index": index, "input_sha256": value_hash(grid)}
            for index, grid in enumerate(inputs)
        ],
        "rival_results": rivals,
        "all_parameter_rivals_refuted": True,
        "label_backend": "RacketBridge.eval_text (content-addressed reuse within this run)",
    }


def check_canonical(oracle: RacketOracle) -> dict[str, Any]:
    ledger = canonical_path(oracle.root)
    records = []
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    records.append(row)
    if not records or any(row.get("program_solution") != canonical_program() for row in records):
        raise ValueError("the exact default program differs from canonical authority")

    results = []
    for pair in canonical_pairs(TASK_ID, root=oracle.root):
        output = oracle.evaluate(Parameters(), pair["input"])
        passed = output == pair["output"]
        results.append({**pair, "executed_output": output, "passed": passed})
        if not passed:
            raise ValueError("executed canonical default disagrees with a canonical label")
    return {
        "status": "passed",
        "canonical_program_byte_identical": True,
        "canonical_program_sha256": CANONICAL_SHA256,
        "canonical_normalized_sha256": sha256_bytes(
            " ".join(canonical_program().split()).encode()
        ),
        "canonical_ledger": str(ledger.relative_to(oracle.root)),
        "canonical_records_sha256": value_hash(records),
        "checked_pairs": len(results),
        "pairs": results,
    }


def check_witness(oracle: RacketOracle) -> dict[str, Any]:
    grid = witness_input()
    outputs = {
        parameters.key: oracle.evaluate(parameters, grid)
        for parameters in all_parameters()
    }
    left, right = all_parameters()
    differences = [
        {
            "row": row,
            "column": col,
            "left": outputs[left.key][row][col],
            "right": outputs[right.key][row][col],
        }
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if outputs[left.key][row][col] != outputs[right.key][row][col]
    ]
    if len(differences) != 2:
        raise ValueError("the lawful witness did not isolate the two outer bar cells")
    return {
        "status": "passed",
        "input": grid,
        "outputs": outputs,
        "pairwise_comparisons": [
            {
                "left": asdict(left),
                "right": asdict(right),
                "differences": differences,
            }
        ],
    }


def source_bindings(root: Path) -> dict[str, str]:
    paths = list(HERE.glob("*.py")) + list(HERE.glob("*.rkt")) + list(HERE.glob("README.md"))
    test_path = HERE.parent.parent / "tests/test_parametric_bar_length.py"
    generator_path = HERE.parent.parent / "generator.py"
    for path in (test_path, generator_path):
        if path.is_file():
            paths.append(path)
    paths.extend(Path(module.__file__).resolve() for module in (racket_bridge, reviewer_support))
    prelude_dir = Path(racket_runtime_status()["prelude_path"]).parent
    paths.extend(prelude_dir.rglob("*.rkt"))
    return {
        str(path.relative_to(root)): sha256_bytes(path.read_bytes())
        for path in sorted(set(paths))
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def invocation() -> dict[str, Any]:
    return {
        "cwd": str(Path.cwd()),
        "argv": [sys.executable, *sys.argv],
        "payload_command": shlex.join([sys.executable, *sys.argv]),
        "python_version": sys.version,
    }


def save_evidence(
    out: Path,
    episodes: list[dict[str, Any]],
    oracle: RacketOracle,
    canonical: dict[str, Any],
    witness: dict[str, Any],
) -> dict[str, Any]:
    private = out / "private"
    private.mkdir(parents=True, exist_ok=True)
    for index, episode in enumerate(episodes):
        public_path = Path("public") / f"episode-{index:03d}.json"
        _write_json(out / public_path, episode["public"])
        episode["public_path"] = str(public_path)
    for parameters in all_parameters():
        path = private / "rules" / f"{parameters.key}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(materialize_program(parameters), encoding="utf-8")
    _write_json(private / "episodes.json", episodes)
    _write_json(private / "canonical_check.json", canonical)
    _write_json(private / "witness.json", witness)
    with (private / "executions.jsonl").open("w", encoding="utf-8") as handle:
        for execution in oracle.executions:
            handle.write(json_bytes(execution).decode() + "\n")

    runtime = racket_runtime_status()
    binary = Path(runtime["resolved_binary"])
    version = subprocess.run(
        [str(binary), "--version"], text=True, capture_output=True, check=True
    )
    summary = {
        "schema": "474634a9f7b7-parametric-bar-length-evidence-v1",
        "status": "passed",
        "scope": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "exit_status": 0,
        "episode_count": len(episodes),
        "seeds": sorted({episode["seed"] for episode in episodes}),
        "settings_exercised": [asdict(parameters) for parameters in all_parameters()],
        "demonstration_pairs": sum(len(episode["train"]) for episode in episodes),
        "query_pairs": sum(len(episode["test"]) for episode in episodes),
        "parameter_rival_comparisons": sum(
            len(episode["rival_results"]) for episode in episodes
        ),
        "all_parameter_rivals_refuted": all(
            episode["all_parameter_rivals_refuted"] for episode in episodes
        ),
        "ambiguities": 0,
        "canonical_pairs_checked": canonical["checked_pairs"],
        "witness_setting_pairs_distinguished": len(witness["pairwise_comparisons"]),
        "actual_racket_evaluations": len(oracle.executions),
        "execution_cache_hits": oracle.cache_hits,
        "invocation": invocation(),
        "source_hashes": source_bindings(oracle.root),
        "program_hashes": {
            parameters.key: sha256_bytes(materialize_program(parameters).encode())
            for parameters in all_parameters()
        },
        "runtime": {
            **runtime,
            "binary_sha256": sha256_bytes(binary.read_bytes()),
            "version_stdout": version.stdout.strip(),
        },
        "main_generator_dependency": True,
        "limits": [
            "This is a proposed task-local prototype, not a production rule change or approval.",
            "Only bar lengths 1 and 3 are studied; the original three-cell bar remains canonical/default.",
            "Inputs come from the selected generator family and labels come only from executed Racket.",
            "Share only individual public/episode-NNN.json challenges; all other evidence is private.",
        ],
    }
    _write_json(private / "receipt.json", summary)
    files = {
        str(path.relative_to(out)): sha256_bytes(path.read_bytes())
        for path in sorted(out.rglob("*"))
        if path.is_file()
    }
    _write_json(
        out / "manifest.json",
        {
            "schema": "474634a9f7b7-parametric-bar-length-files-v1",
            "scope": "private authoring evidence",
            "files": files,
        },
    )
    return summary


def _write_public_examples(path: Path, episodes: list[dict[str, Any]]) -> None:
    if path.exists():
        raise ValueError(f"public example directory already exists: {path}")
    path.mkdir(parents=True)
    for index, episode in enumerate(episodes):
        _write_json(path / f"episode-{index:03d}.json", episode["public"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser(
        "verify", help="execute both settings, canonical labels, and a separating witness"
    )
    verify.add_argument(
        "--seed",
        type=int,
        action="append",
        help="repeat for deterministic episode seeds; default: 0 and 17",
    )
    verify.add_argument("--out", required=True, type=Path)
    verify.add_argument("--write-public", type=Path)

    episode = commands.add_parser("episode", help="materialize one fixed-setting episode")
    episode.add_argument("--seed", required=True, type=int)
    episode.add_argument("--bar-length", type=int, choices=BAR_LENGTHS)
    episode.add_argument("--sample-parameters", action="store_true")
    episode.add_argument("--train", default=4, type=int)
    episode.add_argument("--test", default=1, type=int)
    episode.add_argument("--out", required=True, type=Path)
    episode.add_argument("--write-public", type=Path)
    args = parser.parse_args(argv)

    if (
        args.command == "episode"
        and args.sample_parameters
        and args.bar_length is not None
    ):
        parser.error("--sample-parameters cannot be combined with --bar-length")
    out = args.out.resolve()
    if out.exists():
        parser.error(f"output already exists; use a new directory: {out}")
    out.mkdir(parents=True)
    oracle = None
    try:
        oracle = RacketOracle()
        canonical = check_canonical(oracle)
        witness = check_witness(oracle)
        if args.command == "verify":
            seeds = args.seed if args.seed is not None else [0, 17]
            episodes = [
                build_episode(
                    seed,
                    parameters,
                    oracle=oracle,
                    parameter_selection="enumerated setting fixed per episode",
                )
                for seed in seeds
                for parameters in all_parameters()
            ]
        else:
            parameters = (
                sample_parameters(args.seed)
                if args.sample_parameters
                else Parameters(
                    DEFAULT_BAR_LENGTH
                    if args.bar_length is None
                    else args.bar_length
                )
            )
            episodes = [
                build_episode(
                    args.seed,
                    parameters,
                    oracle=oracle,
                    n_train=args.train,
                    n_test=args.test,
                    parameter_selection=(
                        "seeded once" if args.sample_parameters else "fixed/default"
                    ),
                )
            ]
        summary = save_evidence(out, episodes, oracle, canonical, witness)
        if args.write_public is not None:
            _write_public_examples(args.write_public.resolve(), episodes)
        print(
            json.dumps(
                {
                    key: summary[key]
                    for key in (
                        "status",
                        "scope",
                        "episode_count",
                        "seeds",
                        "actual_racket_evaluations",
                        "canonical_pairs_checked",
                        "parameter_rival_comparisons",
                        "ambiguities",
                    )
                },
                sort_keys=True,
            )
        )
        return 0
    except Exception as exc:
        _write_json(
            out / "private/failure.json",
            {
                "status": "error",
                "scope": "prototype",
                "exit_status": 2,
                "invocation": invocation(),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "completed_executions": [] if oracle is None else oracle.executions,
            },
        )
        print(f"prototype failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if oracle is not None:
            oracle.close()


if __name__ == "__main__":
    raise SystemExit(main())
