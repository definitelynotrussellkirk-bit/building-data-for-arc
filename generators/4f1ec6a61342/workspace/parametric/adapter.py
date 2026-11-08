"""Native adapter for direct and height-relay chamber selection."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_PROTOTYPE_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_arc_4f1ec6a61342_parametric_prototype", _PROTOTYPE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)

CANONICAL_PROGRAM = '(rule!\n  (let ((target-count (at g 0 0))\n        (seen (make-hash)))\n    (define out (grid-from-fn (rows g) (cols g) (lambda (r c) (if (= (at g r c) 5) 5 0))))\n    (for* ([r (in-range (rows g))] [c (in-range (cols g))])\n      (unless (or (hash-has-key? seen (cons r c)) (= (at g r c) 5) (and (= r 0) (= c 0)))\n        (hash-set! seen (cons r c) #t)\n        (when (or (= (at g r c) 0) (= (at g r c) 2))\n          (define queue (list (cons r c)))\n          (define cells (list))\n          (define seeds 0)\n          (let bfs ([step 0])\n            (unless (empty? queue)\n              (let ((cur (first queue)))\n                (set! queue (rest queue))\n                (set! cells (cons (list (car cur) (cdr cur)) cells))\n                (when (= (at g (car cur) (cdr cur)) 2) (set! seeds (+ seeds 1)))\n                (for ([d (in-list cardinal-deltas)])\n                  (let ((nr (+ (car cur) (first d)))\n                        (nc (+ (cdr cur) (second d))))\n                    (when (and (in-bounds? nr nc (rows g) (cols g))\n                               (not (hash-has-key? seen (cons nr nc)))\n                               (not (= (at g nr nc) 5))\n                               (not (and (= nr 0) (= nc 0))))\n                      (hash-set! seen (cons nr nc) #t)\n                      (set! queue (append queue (list (cons nr nc))))))))\n              (bfs (+ step 1))))\n          (when (= seeds target-count)\n            (set! out (paint-cells out cells 8))))))\n    out))'
HEIGHT_RELAY_PROGRAM = '(rule!\n  (let ((target-count (at g 0 0))\n        (seen (make-hash))\n        (rooms-data (list)))\n    (define out (grid-from-fn (rows g) (cols g) (lambda (r c) (if (= (at g r c) 5) 5 0))))\n    (for* ([r (in-range (rows g))] [c (in-range (cols g))])\n      (unless (or (hash-has-key? seen (cons r c)) (= (at g r c) 5) (and (= r 0) (= c 0)))\n        (hash-set! seen (cons r c) #t)\n        (when (or (= (at g r c) 0) (= (at g r c) 2))\n          (define queue (list (cons r c)))\n          (define cells (list))\n          (define seeds 0)\n          (define min-r r)\n          (define max-r r)\n          (let bfs ([step 0])\n            (unless (empty? queue)\n              (let ((cur (first queue)))\n                (set! queue (rest queue))\n                (set! cells (cons (list (car cur) (cdr cur)) cells))\n                (set! min-r (min min-r (car cur)))\n                (set! max-r (max max-r (car cur)))\n                (when (= (at g (car cur) (cdr cur)) 2) (set! seeds (+ seeds 1)))\n                (for ([d (in-list cardinal-deltas)])\n                  (let ((nr (+ (car cur) (first d)))\n                        (nc (+ (cdr cur) (second d))))\n                    (when (and (in-bounds? nr nc (rows g) (cols g))\n                               (not (hash-has-key? seen (cons nr nc)))\n                               (not (= (at g nr nc) 5))\n                               (not (and (= nr 0) (= nc 0))))\n                      (hash-set! seen (cons nr nc) #t)\n                      (set! queue (append queue (list (cons nr nc))))))))\n              (bfs (+ step 1))))\n          (set! rooms-data (cons (list cells seeds (+ 1 (- max-r min-r))) rooms-data)))))\n    (define relay-count 0)\n    (for ([room (in-list rooms-data)])\n      (when (= (second room) target-count)\n        (set! relay-count (third room))))\n    (for ([room (in-list rooms-data)])\n      (when (= (second room) relay-count)\n        (set! out (paint-cells out (first room) 8))))\n    out))'
_PROGRAMS = {"direct": CANONICAL_PROGRAM, "height_relay": HEIGHT_RELAY_PROGRAM}


def _mode(settings: dict) -> str:
    if not isinstance(settings, dict) or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in _PROGRAMS:
        raise ValueError("unknown chamber-selection mode")
    return mode


def program(settings: dict) -> str:
    return _PROGRAMS[_mode(settings)]


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    mode = _PROTOTYPE.validate_request(seed, settings, demos, queries)
    pairs = _PROTOTYPE.generate_pairs(seed, demos, queries, mode)
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(settings),
    }
