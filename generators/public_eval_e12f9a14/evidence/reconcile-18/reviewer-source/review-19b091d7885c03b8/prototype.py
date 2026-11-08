"""Native parametric episode layer for public_eval_e12f9a14."""
from __future__ import annotations

from pathlib import Path
import copy
import hashlib
import importlib
import importlib.util
import json
import random
import sys

TASK_ID = "public_eval_e12f9a14"
HERE = Path(__file__).resolve().parent
HOME = Path(__file__).resolve().parents[2]


def _load_adjacent_generator():
    """Load the exact task-local source with dependencies from the same snapshot.

    Public task-test snapshots intentionally omit the canonical ledger used by
    ``reviewer_support.find_root``. Resolving through the packet sibling would
    silently leave the staged tree. This bounded loader instead binds the
    adjacent generator.py and the snapshot's own shared/runtime package.
    """
    root = HOME.parents[1]
    source = HOME / "generator.py"
    runtime = root / "shared/runtime"
    package_root = (runtime / "puzzle_generators").resolve()
    if (
        source.is_symlink()
        or not source.is_file()
        or not source.resolve().is_relative_to(root)
        or not package_root.is_dir()
        or not package_root.is_relative_to(root)
    ):
        raise ImportError("task-local generator/runtime snapshot is incomplete")

    def check_cached_dependencies() -> None:
        for name, module in tuple(sys.modules.items()):
            if name != "puzzle_generators" and not name.startswith("puzzle_generators."):
                continue
            origins = list(getattr(module, "__path__", []))
            origin = getattr(module, "__file__", None)
            if origin:
                origins.append(origin)
            if not origins or any(not Path(value).resolve().is_relative_to(package_root) for value in origins):
                raise ImportError(f"{name} belongs to another source tree; use a fresh process for {root}")

    check_cached_dependencies()
    body = source.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    name = "_public_adjacent_" + hashlib.sha256(str(source).encode()).hexdigest() + "_" + digest
    existing = sys.modules.get(name)
    if existing is not None:
        return existing, source, digest
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    before = list(sys.path)
    try:
        sys.path.insert(0, str(runtime))
        importlib.import_module("puzzle_generators")
        check_cached_dependencies()
        sys.modules[name] = module
        exec(compile(body, str(source), "exec"), module.__dict__)
        check_cached_dependencies()
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.path[:] = before
    return module, source, digest


_base, _source, _source_sha256 = _load_adjacent_generator()

_int = _base._int
trace = _base.trace
solve = _base.solve
sample = _base.sample
COLLISION_RULES = _base.COLLISION_RULES
RIVALS = _base.RIVALS


def settings(value: object) -> str:
    if (
        type(value) is not dict
        or set(value) != {"collision_rule"}
        or type(value["collision_rule"]) is not str
        or value["collision_rule"] not in COLLISION_RULES
    ):
        raise ValueError("settings must contain exactly one declared collision_rule")
    return value["collision_rule"]


def program(value: object) -> str:
    rule = settings(value)
    source = (HERE / "canonical.rkt").read_text()
    if rule == "vector_sum":
        return source
    needle = "(define collision-rule 'vector_sum)"
    if source.count(needle) != 1:
        raise ValueError("canonical collision declaration drifted")
    return source.replace(needle, "(define collision-rule 'stop)")


def generate(seed: object, value: object, demos: object, queries: object) -> dict[str, object]:
    rule = settings(value)
    _int(seed, 0, 2**63 - 1, "seed")
    _int(demos, 2, 6, "demos")
    _int(queries, 4, 4, "queries")
    banks = {
        "train": [sample(seed, index) for index in range(demos)],
        "test": [sample(seed, 100 + index) for index in range(4)],
    }
    inputs = [grid for split in ("train", "test") for grid in banks[split]]
    if len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) != len(inputs):
        raise ValueError("episode contains duplicate inputs")
    return {
        "train": [dict(input=grid, output=solve(grid, rule)) for grid in banks["train"]],
        "test": [dict(input=grid, output=solve(grid, rule)) for grid in banks["test"]],
        "program_solution": program(value),
    }


def public_turns(episode: object, presentation_seed: object, stop_after: object = 4) -> list[dict[str, object]]:
    _int(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    _int(stop_after, 1, 4, "stop_after")
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if len(episode["test"]) != 4:
        raise ValueError("materialize the complete four-query bank first")
    order = list(range(4))
    random.Random(presentation_seed).shuffle(order)
    train = [
        {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
        for pair in episode["train"]
    ]
    return [
        {"train": copy.deepcopy(train), "test": [{"input": copy.deepcopy(episode["test"][index]["input"])}]}
        for index in order[:stop_after]
    ]
