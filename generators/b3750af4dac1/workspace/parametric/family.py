"""Native room-signature family with a post-match graph-neighbor relay.

``match_only`` is the exact canonical program. ``mark_match_neighbors`` first
computes the canonical one-hot exact-signature match strip, then uses the
selected strip position to recover the matching room and marks all candidate
rooms joined to it by color-7 doorways with color 4. The sampler guarantees
that an area-only intermediate chooses a different room with a different
neighbor set, making the stage-A output causally necessary.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_ID = "b3750af4dac1"
FINISHES = ("match_only", "mark_match_neighbors")
DEFAULT_FINISH = "match_only"
MAX_SEARCH_ATTEMPTS = 64

# Profiles are fixed by visible position, so prefixes are stable and settings
# share byte-identical inputs.
TRAIN_PROFILES = (
    ("easy", {}),
    ("easy", {"macro_r": 2, "macro_c": 4, "room_h": 3, "room_w": 4}),
    ("medium", {"macro_r": 3, "macro_c": 4, "room_h": 4, "room_w": 5}),
    ("medium", {"macro_r": 3, "macro_c": 5, "room_h": 5, "room_w": 4}),
    ("hard", {"macro_r": 4, "macro_c": 5, "room_h": 6, "room_w": 6}),
    ("hard", {"macro_r": 5, "macro_c": 4, "room_h": 7, "room_w": 5}),
)
QUERY_PROFILES = (
    ("medium", {"macro_r": 2, "macro_c": 5, "room_h": 4, "room_w": 6}),
    ("hard", {"macro_r": 3, "macro_c": 5, "room_h": 6, "room_w": 7}),
    ("hard", {"macro_r": 4, "macro_c": 6, "room_h": 5, "room_w": 4}),
    ("hard", {"macro_r": 5, "macro_c": 5, "room_h": 4, "room_w": 4}),
)


def _load_production():
    path = HERE.parents[1] / "generator.py"
    name = "_b3750af4dac1_production_" + hashlib.sha256(str(path).encode()).hexdigest()
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PRODUCTION = _load_production()
_ATTEMPTS: dict[tuple[tuple[int, ...], ...], int] = {}


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _finish(settings: Any) -> str:
    if type(settings) is not dict:
        raise TypeError("settings must be an exact dictionary")
    if set(settings) != {"finish"}:
        raise ValueError("settings must name exactly finish")
    finish = settings["finish"]
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError("finish must be match_only or mark_match_neighbors")
    return finish


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return [row[:] for row in value]


def _fingerprint(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _room_helpers() -> str:
    # This is the canonical room extraction/door-graph logic, retained locally
    # so every non-default program remains standalone and source-bound.
    return r"""
  (define (wall? v) (member? v (list 1 7 9)))
  (define (make-room id cells)
    (let* ((bb (bbox-of-cells cells))
           (r (first bb)) (c (second bb))
           (h (+ 1 (- (third bb) r)))
           (w (+ 1 (- (fourth bb) c))))
      (list id cells (list r c h w))))
  (define (room-id room) (first room))
  (define (room-cells room) (second room))
  (define (room-bbox room) (third room))
  (define (room-r room) (first (room-bbox room)))
  (define (room-c room) (second (room-bbox room)))
  (define (room-order rooms)
    (sort (map room-id rooms)
          (lambda (a b)
            (let ((ra (list-ref rooms a)) (rb (list-ref rooms b)))
              (if (= (room-r ra) (room-r rb))
                  (< (room-c ra) (room-c rb))
                  (< (room-r ra) (room-r rb)))))))
  (define (extract-room-data grid)
    (define seen (make-hash))
    (define cell-to-rid (make-hash))
    (define rooms (list))
    (for* ((r (in-range (rows grid))) (c (in-range (cols grid))))
      (when (and (not (wall? (at grid r c)))
                 (not (hash-has-key? seen (list r c))))
        (define cells
          (connected-region grid r c
                            (lambda (rr cc v) (not (wall? v))) 4))
        (define id (length rooms))
        (for ((p (in-list cells)))
          (hash-set! seen p #t)
          (hash-set! cell-to-rid p id))
        (set! rooms (append rooms (list (make-room id cells))))))
    (list rooms cell-to-rid))
  (define (room-graph grid)
    (let* ((data (extract-room-data grid))
           (rooms (first data))
           (cell-to-rid (second data))
           (adj (make-hash)))
      (for ((room (in-list rooms)))
        (hash-set! adj (room-id room) (list)))
      (define (add-edge a b)
        (hash-set! adj a
                   (sort (remove-duplicates
                          (cons b (hash-ref adj a (list)))) <))
        (hash-set! adj b
                   (sort (remove-duplicates
                          (cons a (hash-ref adj b (list)))) <)))
      (for* ((r (in-range (rows grid))) (c (in-range (cols grid))))
        (when (= (at grid r c) 7)
          (define ids
            (remove-duplicates
             (filter number?
                     (map (lambda (d)
                            (hash-ref cell-to-rid
                                      (list (+ r (first d))
                                            (+ c (second d))) #f))
                          cardinal-deltas))))
          (for* ((a (in-list ids)) (b (in-list ids)))
            (when (< a b) (add-edge a b)))))
      (list rooms adj cell-to-rid)))
"""


def _relay_program(*, selection: str, marking: str) -> str:
    """Build a standalone protected-Racket alternative.

    selection: exact | area | degree | first
    marking: neighbors | strip-neighbors | query-neighbors | all | selected-only
    """
    from puzzle_generators.rule_wrap import wrap_rule

    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    canonical_fn = wrap_rule(canonical)
    helpers = _room_helpers()
    if selection == "exact":
        selection_source = f"""
  (define intermediate ({canonical_fn} g))
  (define selected
    (first (filter (lambda (i) (= (at intermediate 0 i) 8))
                   (range 0 (cols intermediate)))))"""
    elif selection in ("area", "degree"):
        metric = "length (room-cells room)" if selection == "area" else "length (hash-ref adj (room-id room))"
        query_metric = "length (room-cells query)" if selection == "area" else "length (hash-ref adj (room-id query))"
        selection_source = f"""
  (define query (list-ref rooms (first order)))
  (define target ({query_metric}))
  (define selected
    (first
     (map first
          (filter
           (lambda (pair)
             (let ((room (list-ref rooms (second pair))))
               (= ({metric}) target)))
           (enumerate-list cands)))))"""
    elif selection == "first":
        selection_source = "\n  (define selected 0)"
    else:
        raise ValueError(selection)

    if marking == "neighbors":
        mark_source = """
  (define selected-room (list-ref rooms (list-ref cands selected)))
  (define marked (hash-ref adj (room-id selected-room)))
  (grid-from-fn 1 (length cands)
                (lambda (r c)
                  (cond ((= c selected) 8)
                        ((member? (list-ref cands c) marked) 4)
                        (else 0))))"""
    elif marking == "strip-neighbors":
        mark_source = """
  (grid-from-fn 1 (length cands)
                (lambda (r c)
                  (cond ((= c selected) 8)
                        ((or (= c (- selected 1)) (= c (+ selected 1))) 4)
                        (else 0))))"""
    elif marking == "query-neighbors":
        mark_source = """
  (define query-room (list-ref rooms (first order)))
  (define marked (hash-ref adj (room-id query-room)))
  (grid-from-fn 1 (length cands)
                (lambda (r c)
                  (cond ((= c selected) 8)
                        ((member? (list-ref cands c) marked) 4)
                        (else 0))))"""
    elif marking == "all":
        mark_source = """
  (grid-from-fn 1 (length cands)
                (lambda (r c) (if (= c selected) 8 4)))"""
    elif marking == "selected-only":
        mark_source = """
  (grid-from-fn 1 (length cands)
                (lambda (r c) (if (= c selected) 8 0)))"""
    else:
        raise ValueError(marking)

    return f"""(rule! (lambda (g)
{helpers}
  (define rg (room-graph g))
  (define rooms (first rg))
  (define adj (second rg))
  (define order (room-order rooms))
  (define cands (rest order)){selection_source}
{mark_source}))"""


def program(settings: dict[str, Any]) -> str:
    finish = _finish(settings)
    canonical = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if finish == "match_only":
        return canonical
    return _relay_program(selection="exact", marking="neighbors")


def counterfactual_program() -> str:
    """Wrong intermediate: select the first same-area room, then relay."""
    return _relay_program(selection="area", marking="neighbors")


def strip_neighbor_program() -> str:
    return _relay_program(selection="exact", marking="strip-neighbors")


def query_neighbor_program() -> str:
    return _relay_program(selection="exact", marking="query-neighbors")


def all_candidate_program() -> str:
    return _relay_program(selection="exact", marking="all")


def area_only_program() -> str:
    return _relay_program(selection="area", marking="selected-only")


def degree_only_program() -> str:
    return _relay_program(selection="degree", marking="selected-only")


def first_candidate_program() -> str:
    return _relay_program(selection="first", marking="selected-only")


def _facts(grid: list[list[int]]) -> dict[str, Any]:
    source = _grid(grid)
    facts = _PRODUCTION._rule_facts(source)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    if len(facts.get("matches", ())) != 1:
        raise ValueError("grid must contain exactly one complete-signature match")
    return facts


def match_state(grid: list[list[int]]) -> dict[str, Any]:
    source = _grid(grid)
    facts = _facts(source)
    order = list(facts["order"])
    candidates = order[1:]
    match_index = int(facts["matches"][0])
    matched_room = candidates[match_index]
    neighbor_positions = {
        index
        for index, room_id in enumerate(candidates)
        if room_id in facts["adjacency"][matched_room]
    }
    query_area = facts["signatures"][0][0]
    same_area = [
        index for index, signature in enumerate(facts["signatures"][1:])
        if signature[0] == query_area
    ]
    if not same_area:
        raise ValueError("grid has no same-area candidate")
    area_only_index = same_area[0]
    area_room = candidates[area_only_index]
    area_neighbor_positions = {
        index
        for index, room_id in enumerate(candidates)
        if room_id in facts["adjacency"][area_room]
    }
    return {
        "intermediate": [row[:] for row in facts["output"]],
        "match_index": match_index,
        "neighbor_positions": sorted(neighbor_positions),
        "area_only_index": area_only_index,
        "area_neighbor_positions": sorted(area_neighbor_positions),
        "candidate_count": len(candidates),
        "search_attempt": _ATTEMPTS.get(_fingerprint(source), -1),
    }


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    finish = _finish(settings)
    source = _grid(grid)
    canonical = _PRODUCTION.rule_mirror(source)
    if finish == "match_only":
        return canonical
    state = match_state(source)
    output = [[0 for _ in range(state["candidate_count"])]]
    output[0][state["match_index"]] = 8
    for index in state["neighbor_positions"]:
        if index != state["match_index"]:
            output[0][index] = 4
    return output


def wrong_intermediate_transform(grid: list[list[int]]) -> list[list[int]]:
    source = _grid(grid)
    state = match_state(source)
    output = [[0 for _ in range(state["candidate_count"])]]
    output[0][state["area_only_index"]] = 8
    for index in state["area_neighbor_positions"]:
        if index != state["area_only_index"]:
            output[0][index] = 4
    return output


def _candidate_seed(seed: int, split: str, index: int, attempt: int) -> tuple[int, int]:
    raw = hashlib.sha256(
        f"b3750af4dac1/neighbor-relay-v1/{seed}/{split}/{index}/{attempt}".encode("ascii")
    ).digest()
    generated_seed = int.from_bytes(raw[:8], "big") & (2**63 - 1)
    sample_index = int.from_bytes(raw[8:12], "big")
    return generated_seed, sample_index


def _profile(split: str, index: int) -> tuple[str, dict[str, int]]:
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    difficulty, overrides = profiles[index]
    return difficulty, dict(overrides)


def _eligible(grid: list[list[int]], split: str, index: int) -> bool:
    try:
        state = match_state(grid)
    except (TypeError, ValueError):
        return False
    if state["match_index"] == state["area_only_index"]:
        return False
    if not state["neighbor_positions"]:
        return False
    if len(state["neighbor_positions"]) >= state["candidate_count"] - 1:
        return False
    if state["neighbor_positions"] == state["area_neighbor_positions"]:
        return False
    selected = state["match_index"]
    strip_neighbors = sorted(
        position
        for position in (selected - 1, selected + 1)
        if 0 <= position < state["candidate_count"]
    )
    if state["neighbor_positions"] == strip_neighbors:
        return False
    facts = _facts(grid)
    order = list(facts["order"])
    query_room = order[0]
    query_neighbors = sorted(
        position
        for position, room_id in enumerate(order[1:])
        if room_id in facts["adjacency"][query_room]
    )
    if state["neighbor_positions"] == query_neighbors:
        return False
    if split == "test" and index == 3:
        if len(grid) != 30 or len(grid[0]) != 30:
            return False
        if sum(cell != 0 for row in grid for cell in row) < 400:
            return False
        if state["candidate_count"] != 24:
            return False
    return True


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    _integer(index, 0, len(profiles) - 1, "index")
    difficulty, overrides = _profile(split, index)
    for attempt in range(MAX_SEARCH_ATTEMPTS):
        generated_seed, sample_index = _candidate_seed(seed, split, index, attempt)
        try:
            grid = _PRODUCTION.generate(
                generated_seed,
                sample_index,
                difficulty=difficulty,
                **overrides,
            )
        except (RuntimeError, ValueError):
            continue
        source = _grid(grid)
        if not _eligible(source, split, index):
            continue
        _ATTEMPTS[_fingerprint(source)] = attempt
        return source
    raise RuntimeError(
        f"bounded sampler exhausted {MAX_SEARCH_ATTEMPTS} attempts for {split}[{index}]"
    )


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    finish = _finish(settings)
    selected = {"finish": finish}
    train: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            target.append({"input": grid, "output": transform(grid, selected)})
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(selected),
        "train": train,
        "test": test,
        "program_solution": program(selected),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(episode) is not dict:
        raise TypeError("episode must be a dictionary")
    if type(query_index) is not int or isinstance(query_index, bool):
        raise ValueError("query_index must be an exact integer")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("query_index is outside the stored query range")
    return {
        "train": deepcopy(train),
        "test": [{"input": deepcopy(test[query_index]["input"])}],
    }
