"""Execute predicted Racket programs against ARC train/test pairs and score them.

This is the whole point of the program-synthesis track: a predicted program is
EXECUTABLE and CHECKABLE, unlike a raw output-grid guess. At inference this
powers generate -> execute -> keep-what-passes (candidate selection), and at
eval it gives an honest train-pass / test-pass signal.

A program is expected to be the canonical `(rule! BODY)` form. In `strict` mode
the verifier rejects garbage around the program (markdown fences with trailing
prose, multiple s-expressions, unbalanced parens) so a correct-looking first
expression can't hide malformed model output. It does NOT require BODY to be a
lambda: our corpus has legitimately point-free gold (`(rule! rotate-ccw)`,
`(rule! (pipe ...))`), let-wrapped lambdas, and `(let ((dummy 0)) (define ...) g)`
grid expressions — which form BODY is is resolved at RUNTIME via `procedure?`.

    from scripts.coder_synth_verify import ProgramVerifier
    v = ProgramVerifier()
    res = v.score(program, train_pairs, test_pairs)
    # res = {"train_pass": 3, "train_total": 3, "solves_train": True,
    #        "test_pass": 1, "test_total": 1, "error": None}

Prediction-file CLI: JSONL records may carry `program`, `completion`, `text`,
`output`, or a list under `candidates`/`programs`, plus `task_id`/`content_hash`.
The CLI reports pass@k after executable train filtering and test scoring against
canonical held-out rows.

This file is a MERGE of three converging contributions (recorded so the lineage
is auditable): the strict-parse framework + pass@k CLI (reviewer gpt55_pro_263
patch 02), the fail-closed error contract (reviewer gpt55_2_60), and the
data-encoding tolerance found by same-session gold dogfooding — `_norm_grid`
(609/4341 canonical rows store grids as ROW-STRINGS) and `_as_pairs` (1239/4350
rows store `test` as a single dict, not a list).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Allow `python3 scripts/coder_synth_verify.py` to import repo-root packages.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arc_repl.racket_bridge import RacketBridge


class ProgramFormatError(ValueError):
    """Candidate text is not exactly one canonical `(rule! ...)` s-expression."""


RULE_PREFIX_RE = re.compile(r"^\(rule!(?:\s|\(|\))")  # ( also ends the rule! token (valid no-space call form)


def _strip_markdown_fence(text: str) -> str:
    s = (text or "").strip()
    if not s.startswith("```"):
        return s
    # Accept a single fenced block; any text outside it is rejected by
    # _single_sexpr(). The opening fence may be ```racket or bare ```.
    m = re.match(r"^```[^\n]*\n(.*)\n```$", s, flags=re.S)
    return m.group(1).strip() if m else s


def _single_sexpr(text: str) -> str:
    """Return the only s-expression in text, or raise on extra/malformed text."""
    s = text.strip()
    if not s:
        raise ProgramFormatError("empty program")
    start = next((i for i, ch in enumerate(s) if not ch.isspace()), None)
    if start is None or s[start] != "(":
        raise ProgramFormatError("program must start with a parenthesized s-expression")
    depth = 0
    in_string = False
    escape = False
    in_line_comment = False
    end = None
    for i, ch in enumerate(s[start:], start):
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            continue
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == ";":
            in_line_comment = True
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise ProgramFormatError("unbalanced closing parenthesis")
            if depth == 0:
                end = i + 1
                break
    if depth != 0 or end is None:
        raise ProgramFormatError("unbalanced parentheses")
    trailing = s[end:].strip()
    if trailing:
        raise ProgramFormatError("extra text after the program")
    return s[start:end]


def _unwrap_rule(program: str, *, strict: bool = True) -> str:
    """Return BODY from `(rule! BODY)`.

    strict: require exactly one clean `(rule! ...)` s-expression (no markdown
    trailing prose, balanced). We deliberately do NOT require BODY to be a
    lambda — point-free and let/grid-expr bodies are valid (see module docstring).
    lenient: best-effort wrapper strip for already-trusted gold text.
    """
    text = _strip_markdown_fence(program)
    # Racket line-comment headers are whitespace, not prose outside the rule.
    # Normalize them before the single-expression gate while preserving strict
    # rejection of any non-comment prefix or suffix.
    from puzzle_generators.rule_wrap import strip_line_comments  # noqa: PLC0415
    text = strip_line_comments(text).strip()
    if not strict:
        body = text.strip()
        if body.startswith("(rule!"):
            body = body[len("(rule!"):].rsplit(")", 1)[0].strip()
        return body
    expr = _single_sexpr(text)
    if not RULE_PREFIX_RE.match(expr):
        raise ProgramFormatError("program must be wrapped as (rule! ...)")
    body = expr[len("(rule!"):-1].strip()
    if not body:
        raise ProgramFormatError("rule! body is empty")
    return body


def _inner_expr(program: str, *, strict: bool = True) -> str:
    """Turn a `(rule! BODY)` program into a grid-valued expression.

    The real `rule!` macro auto-binds `g`, `h`, and `w` for BODY-form programs
    (CLAUDE.md / docs/RACKET_DSL.md: "auto-bound g/h/w"). The verifier must
    emulate that scope, otherwise a canonical body such as
    `(rule! (grid-from-fn h w ...))` is rejected as `h: undefined` even though it
    is valid under the DSL contract (~786 body-form corpus programs use h/w).

    Evaluate BODY once with `g`/`h`/`w` defined and decide at RUNTIME: a
    procedure (lambda, point-free transform, `(pipe ...)`, let-wrapped lambda) is
    applied to `g`; anything else (a `(let (...) (define ...) ... g ...)` grid
    expression) is already the output grid. This single rule covers every BODY
    form in the corpus without a brittle text heuristic. The h/w bindings are
    harmlessly unused by lambda-form bodies that take their own grid arg.
    """
    body = _unwrap_rule(program, strict=strict)
    # Bare-bridge normalization, shared with the producer path
    # (puzzle_generators.rule_wrap / wrap_rule): the bridge flattens
    # newlines (comments would eat the rest of the rule) and has no REPL
    # `{K V ...}` dict-literal or for-shorthand reader. Without this, a
    # valid canonical rule using `{...}` crashes here with
    # "application: not a procedure" while rule_smoke passes it.
    from puzzle_generators.rule_wrap import (  # noqa: PLC0415
        convert_dict_literals,
        convert_for_shorthand,
        strip_line_comments,
    )
    body = convert_for_shorthand(
        convert_dict_literals(strip_line_comments(body))
    )
    return (f"(let* ((h (rows g)) (w (cols g)) (candidate {body})) "
            f"(if (procedure? candidate) (candidate g) candidate))")


def _norm_grid(g):
    """Coerce a grid to list-of-int-rows.

    Canonical stores some grids as row-strings ("0050" -> [0,0,5,0]); the bridge
    speaks int-lists. Normalizing both the input we feed and the output we
    compare against keeps the verifier encoding-agnostic.
    """
    if isinstance(g, list) and g and isinstance(g[0], str):
        return [[int(ch) for ch in row] for row in g]
    return g


def _grids_equal(a, b) -> bool:
    return _norm_grid(a) == _norm_grid(b)


def _as_pairs(pairs):
    """Coerce a pairs field to a list of {input,output} dicts.

    Canonical stores `test` as a SINGLE dict for ~1239 rows (one test pair) and
    as a list elsewhere; `train` is always a list. Iterating a bare dict yields
    its keys, so normalize to a list before scoring.
    """
    if pairs is None:
        return []
    if isinstance(pairs, dict):
        return [pairs]
    return pairs


class ProgramVerifier:
    """Reusable Racket-bridge wrapper for scoring predicted programs."""

    def __init__(self, bridge: RacketBridge | None = None, *, strict: bool = True,
                 timeout: float | None = None):
        self.strict = strict
        if bridge is not None:
            self.bridge = bridge
        else:
            kw = {} if timeout is None else {"timeout": timeout}
            self.bridge = RacketBridge(**kw)

    def close(self):
        shutdown = getattr(self.bridge, "shutdown", None)
        if shutdown:
            shutdown()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def apply(self, program: str, grid):
        """Run program on one grid; returns the output grid (raises on error)."""
        # Restart the bridge if a PRIOR program crashed/timed-out the subprocess.
        # Without this, one bad candidate leaves the Racket process dead and EVERY
        # subsequent candidate fails with "Racket process is not running" — which
        # silently zeroed 17/48 candidates in the first v2 validation run (they were
        # never actually evaluated). Fail-and-recover, not fail-and-cascade.
        alive = getattr(self.bridge, "alive", None)
        start = getattr(self.bridge, "_start", None)
        if callable(alive) and callable(start) and not self.bridge.alive():
            start()
        self.bridge.define_grid("g", _norm_grid(grid))
        return self.bridge.eval_text(_inner_expr(program, strict=self.strict))

    def score(self, program: str, train_pairs, test_pairs=None) -> dict:
        """Pass counts over train (and optionally test) pairs.

        Never raises: malformed/crashing programs score 0 with `error` set,
        which is exactly the signal a candidate-selection loop wants.
        """
        train_pairs = _as_pairs(train_pairs)
        # Test-blind rows (pairs shipped without an "output") cannot be
        # scored; excluding them from test_total keeps the denominator
        # honest instead of KeyError-aborting the whole score (which also
        # zeroed the already-counted train passes).
        test_pairs = [
            p for p in _as_pairs(test_pairs) if "output" in p
        ]
        res = {"train_pass": 0, "train_total": len(train_pairs),
               "test_pass": 0, "test_total": len(test_pairs),
               "solves_train": False, "error": None}
        try:
            # Parse/format-check once before mutating the Racket namespace.
            _inner_expr(program, strict=self.strict)
            for p in train_pairs:
                got = self.apply(program, p["input"])
                if _grids_equal(got, p["output"]):
                    res["train_pass"] += 1
            for p in test_pairs:
                got = self.apply(program, p["input"])
                if _grids_equal(got, p["output"]):
                    res["test_pass"] += 1
        except Exception as e:  # malformed program / bridge error -> 0, recorded
            # Fail-closed contract for candidate selection (reviewer gpt55_2_60):
            # ANY crash makes the program a non-solver, even if some pairs were
            # already counted — otherwise a candidate that passes train then
            # crashes on a held-out pair could report solves_train=True, unsafe
            # for execute-and-select.
            res["error"] = repr(e)[:300]
            res["train_pass"] = 0
            res["test_pass"] = 0
        res["solves_train"] = (res["error"] is None
                               and res["train_total"] > 0
                               and res["train_pass"] == res["train_total"])
        return res


def _candidate_programs(record: dict) -> list[str]:
    for key in ("candidates", "programs", "predictions"):
        vals = record.get(key)
        if isinstance(vals, list):
            out = []
            for v in vals:
                if isinstance(v, str):
                    out.append(v)
                elif isinstance(v, dict):
                    out.extend(_candidate_programs(v))
            return out
    for key in ("program", "completion", "text", "output"):
        val = record.get(key)
        if isinstance(val, str) and val.strip():
            return [val]
    return []


_BY_TASK_ID_KEY = "__by_task_id__"


def load_canonical(path: str | Path) -> dict:
    """Index canonical rows by content_hash plus task_id metadata.

    content_hash is unique and is the preferred join key. task_id is NOT unique
    in this corpus because augmented variants keep the parent task_id. A subtle
    namespace trap: many original rows have `content_hash == task_id`, so a flat
    `rows.get(task_id)` can still hit the original content_hash even when that
    task_id is ambiguous. Use `lookup_canonical()` so the caller's key type is
    respected.
    """
    rows = {}
    by_task_id = {}
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("content_hash"):
                rows[row["content_hash"]] = row
            if row.get("task_id"):
                by_task_id.setdefault(row["task_id"], []).append(row)
    rows[_BY_TASK_ID_KEY] = by_task_id
    # Backward-compatible singleton task_id aliases. Ambiguous IDs are deliberately
    # NOT inserted as aliases; lookup_canonical() also avoids the content_hash==
    # task_id collision by consulting this map only when the input was a task_id.
    for tid, vals in by_task_id.items():
        if len(vals) == 1 and tid not in rows:
            rows[tid] = vals[0]
    return rows


def lookup_canonical(index: dict, *, content_hash: str | None = None,
                     task_id: str | None = None) -> dict | None:
    """Join a prediction row to canonical data without hash/task namespace leaks."""
    if content_hash:
        row = index.get(content_hash)
        if isinstance(row, dict):
            return row
    if task_id:
        vals = index.get(_BY_TASK_ID_KEY, {}).get(task_id, [])
        if len(vals) == 1:
            return vals[0]
    return None


def eval_prediction_file(predictions: str | Path, canonical: str | Path, *,
                         max_candidates: int, strict: bool) -> dict:
    rows = load_canonical(canonical)
    totals = {"records": 0, "known_tasks": 0, "with_candidates": 0,
              "train_pass_at_k": 0, "test_pass_at_k": 0, "with_test": 0,
              "candidate_scores": 0}
    errors = {}
    with ProgramVerifier(strict=strict) as verifier, open(predictions) as f:
        for line in f:
            if not line.strip():
                continue
            totals["records"] += 1
            rec = json.loads(line)
            row = lookup_canonical(rows, content_hash=rec.get("content_hash"),
                                   task_id=rec.get("task_id"))
            if row is None:
                continue
            totals["known_tasks"] += 1
            cands = _candidate_programs(rec)[:max_candidates]
            if not cands:
                continue
            totals["with_candidates"] += 1
            test_total = len(_as_pairs(row.get("test")))
            if test_total:
                totals["with_test"] += 1
            train_ok = test_ok = False
            train_pairs = row.get("train") or []
            test_pairs = row.get("test") or []
            for cand in cands:
                # Keep pass@k train accounting train-blind. score() fail-closes by
                # zeroing BOTH train and test counts on any exception (2_60's
                # selection-safety contract); scoring train+test TOGETHER would let
                # a hidden-test crash erase a candidate that solved all demos. So
                # score train and test in SEPARATE calls (disjoint pair sets) — the
                # score() fail-closed contract is preserved per call.
                train_score = verifier.score(cand, train_pairs, [])
                totals["candidate_scores"] += 1
                if train_score.get("error"):
                    errors[train_score["error"]] = errors.get(train_score["error"], 0) + 1
                if not train_score.get("solves_train"):
                    continue
                train_ok = True
                if test_total:
                    test_score = verifier.score(cand, [], test_pairs)
                    if test_score.get("error"):
                        errors[test_score["error"]] = errors.get(test_score["error"], 0) + 1
                    if test_score.get("test_total", 0) and test_score.get("test_pass") == test_score.get("test_total"):
                        test_ok = True
            totals["train_pass_at_k"] += int(train_ok)
            totals["test_pass_at_k"] += int(test_ok)
    denom = max(1, totals["known_tasks"])
    test_denom = max(1, totals["with_test"])
    return {
        **totals,
        "max_candidates": max_candidates,
        "strict": strict,
        "train_pass_at_k_pct": round(100 * totals["train_pass_at_k"] / denom, 2),
        "test_pass_at_k_pct": round(100 * totals["test_pass_at_k"] / test_denom, 2),
        "top_errors": sorted(errors.items(), key=lambda kv: kv[1], reverse=True)[:20],
    }


def self_test(canonical: str | Path, n: int, *, strict: bool) -> dict:
    ok = bad = err = seen = 0
    with ProgramVerifier(strict=strict) as v, open(canonical) as f:
        for line in f:
            if seen >= n:
                break
            row = json.loads(line)
            prog = (row.get("program_solution") or "").strip()
            if not prog or len(row.get("train") or []) < 1:
                continue
            seen += 1
            r = v.score(prog, row["train"], row.get("test"))
            if r["error"]:
                err += 1
                print(f"  ERR {row['task_id']}: {r['error'][:120]}")
            elif r["solves_train"]:
                ok += 1
            else:
                bad += 1
                print(f"  MISS {row['task_id']}: train {r['train_pass']}/{r['train_total']}")
    return {"seen": seen, "solves_train": ok, "miss": bad, "error": err, "strict": strict}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Score Racket program-synthesis predictions.")
    ap.add_argument("--canonical", default="data/canonical/puzzles.jsonl")
    ap.add_argument("--predictions", default=None,
                    help="JSONL predictions to score; omit for gold self-test")
    ap.add_argument("--max-candidates", type=int, default=8)
    ap.add_argument("--self-test", type=int, default=25)
    ap.add_argument("--strict", action=argparse.BooleanOptionalAction, default=True,
                    help="reject programs with extra text / multiple s-expressions")
    a = ap.parse_args(argv)

    if a.predictions:
        out = eval_prediction_file(a.predictions, a.canonical,
                                   max_candidates=a.max_candidates, strict=a.strict)
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        out = self_test(a.canonical, a.self_test, strict=a.strict)
        print("\ngold-program self-verify: " + json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
