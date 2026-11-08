"""Racket-backed forward/reverse edit-stencil episodes; proposed, not admitted."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "8a851bf5cdd7"
SCHEMA = "arcpuzzles-stencil-prototype-v1"
HOME = Path(__file__).resolve().parent
DIRECTIONS = ("forward", "reverse")
COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
# Input width = 3 * panel_w + 2. Equal panels cannot produce width 30.
QUERY_PROFILES = ((3, 3, "balanced"), (6, 5, "sparse"),
                  (15, 7, "dense"), (30, 9, "balanced"))
DEMO_PROFILES = ((3, 3, "balanced"), (5, 4, "sparse"),
                 (7, 5, "dense"), (4, 6, "balanced"),
                 (9, 4, "sparse"), (8, 6, "dense"))


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings):
    if (type(settings) is not dict or set(settings) != {"direction"}
            or type(settings["direction"]) is not str
            or settings["direction"] not in DIRECTIONS):
        raise ValueError("settings must contain exactly direction=forward|reverse")
    return {"direction": settings["direction"]}


def program(settings):
    direction = settings_value(settings)["direction"]
    return (HOME / "rules" / f"{direction}.rkt").read_text(encoding="utf-8")


def strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid requires rectangular rows and exact integer colors 0..9")
    return grid


def panels(grid):
    strict_grid(grid)
    ph, width = len(grid), len(grid[0])
    if not 3 <= ph <= 30 or (width - 2) % 3 or not 3 <= (width - 2) // 3 <= 9:
        raise ValueError("input requires 3 equal panels, height3..30 and panel width3..9")
    pw = (width - 2) // 3
    if any(row[pw] != 8 or row[2 * pw + 1] != 8 for row in grid):
        raise ValueError("input requires two full color-8 separators")
    result = [[[row[p * (pw + 1) + c] for c in range(pw)] for row in grid]
              for p in range(3)]
    palettes = [{v for row in panel for v in row if v} for panel in result]
    if (any(len(p) != 1 or not p <= set(COLORS) for p in palettes)
            or palettes[0] != palettes[1] or palettes[0] == palettes[2]):
        raise ValueError("A/B need one shared nonzero color; C needs another; 8 is reserved")
    return result


class RacketEngine:
    """One protected bridge, reused by bounded probes and bulk episode exports."""

    def __init__(self):
        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("A live protected Racket bridge is required")
        self.evaluations = 0
        self._wrapped = {}

    def apply(self, source, grid):
        strict_grid(grid)
        wrapped = self._wrapped.setdefault(source, wrap_rule(source))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        self.evaluations += 1
        return strict_grid(self.bridge.eval_text(f"({wrapped} {literal})"))

    def close(self):
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


@contextmanager
def _engine(existing):
    if existing is None:
        with RacketEngine() as created:
            yield created
    else:
        yield existing


def _rng(seed, domain, index=0, attempt=0):
    key = json.dumps([TASK_ID, SCHEMA, seed, domain, index, attempt], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def sample_input(seed, domain, index, profile, attempt=0):
    """Construct all eight occupancy triples, then vary the remaining content.

    No settings enter this sampler. Eight witnesses are scattered over the actual
    panel, including its corners; the rest is a sparse/dense/balanced random field.
    """
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 1000, "index")
    integer(attempt, 0, 31, "attempt")
    if domain not in {"demo", "query"}:
        raise ValueError("domain must be demo or query")
    ph, pw, density = profile
    integer(ph, 3, 30, "panel height")
    integer(pw, 3, 9, "panel width")
    if density not in {"sparse", "dense", "balanced"}:
        raise ValueError("unknown density profile")
    rng = _rng(seed, domain, index, attempt)
    base, query = rng.sample(COLORS, 2)
    probability = {"sparse": 0.14, "dense": 0.86, "balanced": 0.5}[density]
    states = [tuple(int(rng.random() < probability) for _ in range(3))
              for _ in range(ph * pw)]
    corners = [0, pw - 1, (ph - 1) * pw, ph * pw - 1]
    other = [i for i in range(ph * pw) if i not in corners]
    anchors = corners + rng.sample(other, 4)
    triples = list(itertools.product((0, 1), repeat=3))
    rng.shuffle(triples)
    for index, triple in zip(anchors, triples):
        states[index] = triple
    result = []
    for r in range(ph):
        fields = [[(query if p == 2 else base) * states[r * pw + c][p]
                   for c in range(pw)] for p in range(3)]
        result.append(fields[0] + [8] + fields[1] + [8] + fields[2])
    panels(result)
    return result


def python_oracle(grid, settings):
    """Independent set-based diagnostic, never the source of retained labels."""
    a, b, c = panels(grid)
    if settings_value(settings)["direction"] == "reverse":
        a, b = b, a
    before = {(r, col) for r, row in enumerate(a) for col, v in enumerate(row) if v}
    after = {(r, col) for r, row in enumerate(b) for col, v in enumerate(row) if v}
    occupied = {(r, col) for r, row in enumerate(c) for col, v in enumerate(row) if v}
    target = (occupied - (before - after)) | (after - before)
    color = next(v for row in c for v in row if v)
    return [[color if (r, col) in target else 0 for col in range(len(c[0]))]
            for r in range(len(c))]


@lru_cache(maxsize=1)
def rival_programs():
    """Ten explicit total rules on the admitted three-panel grammar."""
    results = {d: program({"direction": d}) for d in DIRECTIONS}
    expressions = {
        "identity": "q",
        "copy_before": "(if b qcolor 0)",
        "copy_after": "(if a qcolor 0)",
        "forward_add_only": "(if (and (not b) a) qcolor q)",
        "forward_delete_only": "(if (and b (not a)) 0 q)",
        "reverse_add_only": "(if (and b (not a)) qcolor q)",
        "reverse_delete_only": "(if (and (not b) a) 0 q)",
        "toggle_changes": "(if (equal? a b) q (if (= q 0) qcolor 0))",
    }
    for name, expression in expressions.items():
        results[name] = """(rule!
          (let* ((pw (quotient (- (cols g) 2) 3))
                 (before (subgrid g 0 0 (- (rows g) 1) (- pw 1)))
                 (after (subgrid g 0 (+ pw 1) (- (rows g) 1) (* 2 pw)))
                 (query (subgrid g 0 (+ (* 2 pw) 2) (- (rows g) 1) (- (cols g) 1)))
                 (qcolor (first (filter (lambda (v) (not (= v 0))) (apply append query)))))
            (grid-from-fn (rows query) (cols query)
              (lambda (r c)
                (let ((b (not (= (at before r c) 0)))
                      (a (not (= (at after r c) 0))) (q (at query r c)))
                  """ + expression + ")))))"
    return results


def check_teaching(train, settings, *, engine=None):
    """Fit declared rules using only demonstration inputs/outputs.

    There is deliberately no query, query answer, metadata certificate, or future
    turn argument. Failed rule execution is an error, never a distinction witness.
    """
    direction = settings_value(settings)["direction"]
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("teaching pair requires input and output")
        panels(pair["input"])
        strict_grid(pair["output"])
    survivors, distinctions = [], {}
    with _engine(engine) as runtime:
        for name, source in rival_programs().items():
            mismatches = [i for i, pair in enumerate(train)
                          if runtime.apply(source, pair["input"]) != pair["output"]]
            if not mismatches:
                survivors.append(name)
            else:
                distinctions[name] = {"first_demonstration": mismatches[0]}
    if survivors != [direction]:
        raise ValueError(f"demonstrations do not identify {direction}; surviving rules={survivors}")
    return {"fit_scope": "demonstrations_only", "survivors": survivors,
            "declared_rivals": list(rival_programs()), "distinctions": distinctions,
            "limits": "Finite named rule family only; not uniqueness over arbitrary programs."}


def _runtime_record(runtime):
    return {k: runtime.identity[k] for k in
            ("backend", "protected", "binary_sha256", "prelude_sha256",
             "bridge_sha256", "boot_script_sha256") if k in runtime.identity}


def _check_evidence(episode, key, expected):
    # JSON comparison preserves bool/int/float distinctions unlike Python ==.
    try:
        observed = json.dumps(episode.get(key), sort_keys=True, allow_nan=False)
        wanted = json.dumps(expected, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid {key} evidence") from error
    if observed != wanted:
        raise ValueError(f"{key} evidence disagrees with executed verification")


def verify_episode(episode, *, engine=None):
    if type(episode) is not dict or episode.get("task_id") != TASK_ID or episode.get("schema") != SCHEMA:
        raise ValueError("wrong episode identity/schema")
    settings = settings_value(episode.get("settings"))
    integer(episode.get("seed"), 0, 2**63 - 1, "seed")
    source = program(settings)
    if episode.get("program_solution") != source:
        raise ValueError("program_solution differs from the selected exact rule")
    _check_evidence(episode, "program_sha256", hashlib.sha256(source.encode()).hexdigest())
    _check_evidence(episode, "variant_approved", False)
    _check_evidence(episode, "training_admitted", False)
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("train/test must be lists")
    integer(len(train), 2, 6, "demos")
    integer(len(test), 1, 4, "queries")
    seen = set()
    for pair in train + test:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("private pairs need exactly input/output")
        panels(pair["input"])
        strict_grid(pair["output"])
        key = json.dumps(pair["input"], separators=(",", ":"))
        if key in seen:
            raise ValueError("duplicate demonstration/query input")
        seen.add(key)
    with _engine(engine) as runtime:
        for split, pairs in (("train", train), ("test", test)):
            for i, pair in enumerate(pairs):
                if runtime.apply(source, pair["input"]) != pair["output"]:
                    raise ValueError(f"{split}[{i}] label does not match executed Racket")
        certificate = check_teaching(train, settings, engine=runtime)
        _check_evidence(episode, "racket", _runtime_record(runtime))
    certificate["queries"] = [{"query_index": i, "label_matches": True,
                               "compatible_rules": certificate["survivors"][:]} for i in range(len(test))]
    _check_evidence(episode, "certificate", certificate)
    return certificate


def generate(seed, settings, demos=3, queries=4, *, engine=None):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    settings = settings_value(settings)
    source = program(settings)
    episode = {"schema": SCHEMA, "task_id": TASK_ID, "seed": seed,
               "settings": settings, "program_solution": source, "train": [], "test": []}
    seen = set()
    with _engine(engine) as runtime:
        for split, domain, count, profiles in (("train", "demo", demos, DEMO_PROFILES),
                                                ("test", "query", queries, QUERY_PROFILES)):
            for i in range(count):
                for attempt in range(32):
                    grid = sample_input(seed, domain, i, profiles[i], attempt)
                    key = json.dumps(grid, separators=(",", ":"))
                    if key not in seen:
                        break
                else:
                    raise ValueError("could not generate a distinct input within32draws")
                seen.add(key)
                output = runtime.apply(source, grid)
                episode[split].append({"input": grid, "output": output})
        episode["certificate"] = check_teaching(episode["train"], settings, engine=runtime)
        episode["certificate"]["queries"] = [
            {"query_index": i, "label_matches": True, "compatible_rules": [settings["direction"]]}
            for i in range(queries)]
        episode["racket"] = _runtime_record(runtime)
    episode["program_sha256"] = hashlib.sha256(source.encode()).hexdigest()
    episode["variant_approved"] = False
    episode["training_admitted"] = False
    return episode
