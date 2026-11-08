"""Disjoint episode curricula for join/cross and cross-area cascade rules.

All old rule texts and both original samplers are retained. The legacy parameter
name names four episode rules; input matching is local to each source branch.
"""
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent


def _adjacent(name):
    path = HERE / (name + ".py")
    spec = importlib.util.spec_from_file_location("_13507_union_" + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


JOIN = _adjacent("join_adapter")
CASCADE = _adjacent("native")
RULES = JOIN.RULES
VALUES = ("none", "horizontal", "vertical", "cross_area_cascade")


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"join_axis"}
            or type(settings["join_axis"]) is not str
            or settings["join_axis"] not in VALUES):
        raise ValueError("settings must contain exactly one supported join_axis rule choice")
    return settings["join_axis"]


def cascade_program():
    # This guard only defines the cascade outside its original admitted grammar.
    # On every original draw its unique anchor and distinct match exist, and the
    # exact authored body still computes B from the actually painted after-a grid.
    source = CASCADE.CASCADE_PROGRAM
    assert source.startswith("(rule!") and source.endswith(")")
    body = source[len("(rule!"):-1].strip()
    guard = """(rule! (let ()
      (define (height obj) (+ 1 (- (obj-r2 obj) (obj-r1 obj))))
      (define (width obj) (+ 1 (- (obj-c2 obj) (obj-c1 obj))))
      (define (eligible? obj)
        (and (= (obj-color obj) 4) (solid-rect? obj)
             (= (modulo (height obj) 2) 1)
             (= (modulo (width obj) 2) 1)))
      (define candidates (filter eligible? (objects g 0)))
      (define maximum (if (empty? candidates) 0 (max-list (map obj-size candidates))))
      (define anchors (filter (lambda (obj) (= (obj-size obj) maximum)) candidates))
      (if (= (length anchors) 1)
          (let* ((anchor (first anchors))
                 (target-area (- (+ (height anchor) (width anchor)) 1))
                 (matches (filter (lambda (obj)
                   (and (not (equal? (obj-cells obj) (obj-cells anchor)))
                        (= (obj-size obj) target-area))) candidates)))
            (if (= (length matches) 1) __CASCADE_BODY__ g))
          g)))"""
    return guard.replace("__CASCADE_BODY__", body)


def program(settings):
    mode = _mode(settings)
    return cascade_program() if mode == "cross_area_cascade" else JOIN.program(settings)


def branch(seed, settings):
    mode = _mode(settings)
    JOIN._integer(seed, 0, 2**63-1, "seed")
    if mode == "cross_area_cascade":
        return "cascade"
    if mode in ("horizontal", "vertical"):
        return "join"
    return "join"


def generate(seed, settings, demos=3, queries=4):
    mode = _mode(settings)
    JOIN._integer(seed, 0, 2**63-1, "seed")
    JOIN._integer(demos, 2, 6, "demos")
    JOIN._integer(queries, 1, 4, "queries")
    if branch(seed, settings) == "join":
        result = JOIN.generate(seed, {"join_axis": mode}, demos, queries)
    else:
        setting = "cross_area_cascade" if mode == "cross_area_cascade" else "all_odd"
        result = CASCADE.generate(seed, {"selection_rule": setting}, demos, queries)
    return {"train": result["train"], "test": result["test"],
            "program_solution": program(settings)}


def public_turn(episode, query_index=0):
    return CASCADE.public_turn(episode, query_index)
