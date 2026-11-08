"""Proposed Boolean-panel analogy, separate from the assigned canonical U rule.

The complete framed pair identifies identity versus binary complement. Apply that
relation to the other group's nonblank panel using an episode-fixed color role.
"""
import argparse
import json
from pathlib import Path
import random

COLOR_ROLES = ("target", "reference")
CUE_MODES = ("identity", "complement")


def _integer(value, name, low=None, high=None):
    if type(value) is not int:
        raise TypeError(name + " must be an integer, not bool")
    if (low is not None and value < low) or (high is not None and value > high):
        raise ValueError(name + " is outside its supported range")
    return value


def _role(role):
    if type(role) is not str or role not in COLOR_ROLES:
        raise ValueError("output color role must be target or reference")
    return role


def _invert(mask):
    return [[1 - v for v in row] for row in mask]


def _count(mask):
    return sum(map(sum, mask))


def _parse(grid):
    if not isinstance(grid, list) or not grid or not all(isinstance(r, list) for r in grid):
        raise ValueError("grid must be a nonempty list of row lists")
    h, w = len(grid), len(grid[0])
    n = (w - 3) // 2
    if not (3 <= n <= 11 and w == 2 * n + 3 and h == 2 * n + 5):
        raise ValueError("expected two framed n by n panel pairs, 3 <= n <= 11")
    if any(len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integers from 0 through 9")
    if any(grid[n + 2]):
        raise ValueError("group separator must be all zero")

    def read_group(top):
        color = grid[top][0]
        if not 1 <= color <= 9:
            raise ValueError("frame color must be nonzero")
        if any(v != color for r in (top, top + n + 1) for v in grid[r]):
            raise ValueError("broken horizontal frame")
        if any(grid[r][c] != color for r in range(top + 1, top + n + 1)
               for c in (0, n + 1, w - 1)):
            raise ValueError("broken vertical frame")
        panels = []
        for left in (1, n + 2):
            values = [row[left:left + n] for row in grid[top + 1:top + n + 1]]
            if any(v not in (0, color) for row in values for v in row):
                raise ValueError("panel foreground must match its frame color")
            mask = [[int(v != 0) for v in row] for row in values]
            if _count(mask) == n * n:
                raise ValueError("nonblank panels must contain both zero and foreground")
            panels.append(mask)
        return color, panels[0], panels[1]

    groups = [read_group(0), read_group(n + 3)]
    if groups[0][0] == groups[1][0]:
        raise ValueError("group colors must be distinct")
    blanks = [sum(_count(m) == 0 for m in group[1:]) for group in groups]
    if sorted(blanks) != [0, 1]:
        raise ValueError("exactly one of the four panels must be blank")
    complete = groups[blanks.index(0)]
    target = groups[blanks.index(1)]
    matches = []
    if complete[1] == complete[2]:
        matches.append("identity")
    if _invert(complete[1]) == complete[2]:
        matches.append("complement")
    if len(matches) != 1:
        raise ValueError("complete pair must identify exactly one operation")
    target_mask = next(m for m in target[1:] if _count(m))
    return matches[0], complete[0], target[0], target_mask


def python_transform(grid, role="target"):
    """Validate the context and independently infer its Boolean relation."""
    _role(role)
    operation, reference_color, target_color, mask = _parse(grid)
    color = target_color if role == "target" else reference_color
    result = mask if operation == "identity" else _invert(mask)
    return [[color * v for v in row] for row in result]


def rule_source(role="target"):
    """Return self-contained ARC Racket source without a hidden per-input cue."""
    _role(role)
    return r"""(rule!
 (lambda (g)
   (define (bad message) (error 'boolean-analogy message))
   (define h (rows g))
   (define w (cols g))
   (define n (quotient (- w 3) 2))
   (define (mask-count m) (apply + (map (lambda (row) (apply + row)) m)))
   (define (invert m) (map (lambda (row) (map (lambda (v) (- 1 v)) row)) m))
   (unless (and (<= 3 n 11) (= w (+ (* 2 n) 3)) (= h (+ (* 2 n) 5)))
     (bad "unsupported panel geometry"))
   (unless (for*/and ([r (range h)] [c (range w)])
             (let ([v (at g r c)]) (and (exact-integer? v) (<= 0 v 9))))
     (bad "cells must be exact integers from 0 through 9"))
   (unless (for/and ([c (range w)]) (= 0 (at g (+ n 2) c)))
     (bad "separator must be zero"))
   (define (read-group top)
     (define color (at g top 0))
     (unless (<= 1 color 9) (bad "frame must be nonzero"))
     (unless (and
              (for*/and ([r (list top (+ top n 1))] [c (range w)])
                (= color (at g r c)))
              (for*/and ([r (range (+ top 1) (+ top n 1))]
                         [c (list 0 (+ n 1) (- w 1))])
                (= color (at g r c))))
       (bad "broken frame"))
     (define (panel left)
       (define m
         (for/list ([r (range (+ top 1) (+ top n 1))])
           (for/list ([c (range left (+ left n))])
             (let ([v (at g r c)])
               (cond [(= v 0) 0] [(= v color) 1]
                     [else (bad "foreign panel color")])))))
       (when (= (mask-count m) (* n n)) (bad "full panel forbidden"))
       m)
     (list color (panel 1) (panel (+ n 2))))
   (define groups (list (read-group 0) (read-group (+ n 3))))
   (when (= (caar groups) (caadr groups)) (bad "group colors must differ"))
   (define (blanks group)
     (length (filter (lambda (m) (= 0 (mask-count m))) (cdr group))))
   (unless (equal? (sort (map blanks groups) <) '(0 1))
     (bad "exactly one blank panel required"))
   (define complete (if (= 0 (blanks (car groups))) (car groups) (cadr groups)))
   (define target (if (= 1 (blanks (car groups))) (car groups) (cadr groups)))
   (define same? (equal? (cadr complete) (caddr complete)))
   (define complement? (equal? (invert (cadr complete)) (caddr complete)))
   (when (equal? same? complement?) (bad "operation is not unique"))
   (define target-mask
     (if (= 0 (mask-count (cadr target))) (caddr target) (cadr target)))
   (define color (if (eq? '@@ROLE@@ 'target) (car target) (car complete)))
   (for/list ([row target-mask])
     (for/list ([v row]) (* color (if same? v (- 1 v)))))))
""".replace("@@ROLE@@", role)


def _asymmetric(mask):
    original = tuple(map(tuple, mask))
    transforms = []
    current = original
    for _ in range(4):
        transforms.append(current)
        transforms.append(tuple(tuple(reversed(row)) for row in current))
        current = tuple(zip(*current[::-1]))
    return all(t != original for t in transforms[1:])


def _sample_mask(rng, n, forbidden=()):
    for _ in range(256):
        bits = rng.getrandbits(n * n)
        mask = [[(bits >> (r * n + c)) & 1 for c in range(n)] for r in range(n)]
        if 0 < _count(mask) < n * n and mask not in forbidden and _asymmetric(mask):
            return mask
    raise RuntimeError("bounded asymmetric mask sampler exhausted")


def _group(left, right, color):
    n = len(left)
    edge = [color] * (2 * n + 3)
    return [edge[:]] + [[color] + [color * v for v in a] + [color]
                       + [color * v for v in b] + [color]
                       for a, b in zip(left, right)] + [edge[:]]


def sample_grid(seed, index, *, cue_mode=None):
    """Changing cue_mode changes only A; B, target C, frame and layout stay fixed."""
    _integer(seed, "seed")
    _integer(index, "index", 0)
    if cue_mode is not None and cue_mode not in CUE_MODES:
        raise ValueError("cue_mode must be identity or complement")
    rng = random.Random((seed << 32) ^ index)
    n = rng.randint(3, 11)
    reference_color, target_color = rng.sample(range(1, 10), 2)
    b = _sample_mask(rng, n)
    c = _sample_mask(rng, n, (b, _invert(b)))
    operation = cue_mode if cue_mode is not None else CUE_MODES[(seed + index) % 2]
    a = [row[:] for row in b] if operation == "identity" else _invert(b)
    reference = [a, b]
    target = [c, [[0] * n for _ in range(n)]]
    if rng.getrandbits(1):
        reference.reverse()
    if rng.getrandbits(1):
        target.reverse()
    groups = [_group(*reference, reference_color), _group(*target, target_color)]
    if rng.getrandbits(1):
        groups.reverse()
    return groups[0] + [[0] * (2 * n + 3)] + groups[1]


def context_counterfactual(seed=17, index=0):
    """Only A changes, reversing every target bit; everything else is identical."""
    return (sample_grid(seed, index, cue_mode="identity"),
            sample_grid(seed, index, cue_mode="complement"))


def sample_episode(seed, *, role="target", input_seed=None, demo_count=2, query_count=4):
    _integer(seed, "seed")
    _role(role)
    _integer(demo_count, "demo_count", 1, 8)
    _integer(query_count, "query_count", 1, 8)
    input_seed = seed if input_seed is None else _integer(input_seed, "input_seed")
    total = demo_count + query_count
    pairs, accepted, seen = [], [], set()
    for index in range(1024):
        # Alternate by accepted position, even if a candidate duplicates.
        grid = sample_grid(input_seed, index, cue_mode=CUE_MODES[(input_seed + len(pairs)) % 2])
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            continue
        seen.add(key)
        accepted.append(index)
        pairs.append({"input": grid, "output": python_transform(grid, role)})
        if len(pairs) == total:
            break
    if len(pairs) != total:
        raise RuntimeError("bounded distinct-input sampler exhausted")
    return {
        "status": "proposed", "seed": seed, "input_seed": input_seed,
        "parameters": {"output_color_role": role},
        "demo_count": demo_count, "query_count": query_count,
        "accepted_indices": accepted,
        "train": pairs[:demo_count], "test": pairs[demo_count:],
        "program": rule_source(role),
        "lineage": {
            "source_evaluation_task": "4c7dc4dd", "source_demo": 2,
            "selected_task": "33f9169a335e", "original_training_parent": "54d82841",
            "relationship_verified": False,
            "scope": "proposed Boolean-analogy specialization; canonical U rule unchanged",
        },
        "teaching_limitations": ([] if demo_count >= 2 else
            ["One demonstration does not exhibit both within-input relation choices."]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--input-seed", type=int)
    parser.add_argument("--role", choices=COLOR_ROLES, default="target")
    parser.add_argument("--demo-count", type=int, default=2)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    episode = sample_episode(args.seed, role=args.role, input_seed=args.input_seed,
                             demo_count=args.demo_count, query_count=args.query_count)
    text = json.dumps(episode, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
