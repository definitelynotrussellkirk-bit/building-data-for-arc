"""Independent task authoring helpers, portable to copied check runtimes."""
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location
from copy import deepcopy
import hashlib
import json
import os
import sys

TASK_ID = "0d5077971eea"


def prepare_imports():
    for parent in Path(__file__).resolve().parents:
        for candidate in (parent, parent / "shared" / "runtime"):
            if (candidate / "reviewer_support.py").is_file():
                sys.path.insert(0, str(candidate))
                return
    raise FileNotFoundError("No portable reviewer support in this tree")


prepare_imports()
from reviewer_support import canonical_pairs, find_root  # noqa: E402


def load_generator(path=None):
    path = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or
                Path(__file__).resolve().parents[1] / "generator.py").resolve()
    spec = spec_from_file_location("task_generator_under_review", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def row_oracle(grid):
    """Independent authority specification: zero key skips; all other keys act."""
    return [[key if c > 0 and value == 8 and key != 0 else value
             for c, value in enumerate(row)] for row in grid for key in [row[0]]]


def observed(grid):
    width = len(grid[0])
    maximum = max((row[1:].count(8) for row in grid if row[0] not in (0, 8)), default=0)
    density = "low" if maximum == 1 else "med" if maximum <= (width - 1) // 2 else "high"
    return {"grid_h": len(grid), "grid_w": width,
            "n_distinct_colors": len({c for row in grid for c in row}),
            "marker_density": density}


def witness_grid():
    return [[0, 3, 0, 8, 0, 0, 0, 0, 0, 0],
            [2, 4, 8, 8, 8, 8, 0, 0, 0, 8],
            [8, 5, 0, 8, 0, 0, 0, 0, 0, 0],
            [0, 0, 8, 0, 0, 0, 0, 0, 0, 0],
            [6, 7, 8, 0, 0, 0, 0, 0, 0, 0]]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def declared_rivals(gen):
    rivals = {}
    for attribute in ("LESSON_COMPETITORS", "SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS"):
        declaration = getattr(gen, attribute, None)
        if not isinstance(declaration, dict) or not declaration:
            raise ValueError(f"{attribute} must declare named callable rivals")
        for name, fn in declaration.items():
            if not isinstance(name, str) or not callable(fn):
                raise ValueError(f"invalid rival declaration {attribute}:{name}")
            rivals[f"{attribute}:{name}"] = fn
    return rivals


def score_window(rivals, demos, queries):
    from reviewer_support import normalize_grid
    result = {}
    for name, fn in rivals.items():
        fits = all(normalize_grid(fn(deepcopy(pair["input"]))) == pair["output"]
                   for pair in demos)
        agrees = all(normalize_grid(fn(deepcopy(pair["input"]))) == pair["output"]
                     for pair in queries)
        result[name] = "refuted" if not fits else "survived_all" if agrees else "ambiguous"
    return result
