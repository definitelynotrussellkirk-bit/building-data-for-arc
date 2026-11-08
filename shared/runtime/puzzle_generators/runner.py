"""Runner — pipes generator output through RacketBridge to produce
validated (input, output) pairs.

Two source-level conversions are required before sending a rule to
RacketBridge:
  - Strip `;` line comments. The bridge flattens newlines to spaces
    when sending to Racket; a comment that survives the flatten will
    eat the entire rest of the rule.
  - Replace `{K V K V ...}` dict literals with
    `(make-immutable-hash (list (cons K V) ...))`. The executor does
    this in `_expr_to_text`; the bare bridge does not.

The runner is the only place generators meet Racket. It owns:
  - Loading the puzzle's rule from data/base/solutions/<task_id>.
  - Wrapping the rule body so it becomes a callable Racket function
    (mirroring what arc_repl.executor._handle_rule does).
  - Spinning a persistent RacketBridge per batch (cold-start
    amortization: ~150ms once vs ~150ms per call).
  - Validating each (input, output) pair.
  - Writing rejected instances to data/generated/.rejected/<task_id>.jsonl.
  - Bundling validated pairs into {train: [...], test: [...]} dicts.

Public entry points:
    run_one(task_id, seed, sample_index, *, n_train=4, n_test=1, **axes)
    run_batch(task_id, n, *, n_train=4, n_test=1, max_retries=3, **axes)

Phase 2.3 of docs/PUZZLE_GENERATOR_ROADMAP.md.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arc_repl.racket_bridge import RacketBridge, RacketBridgeError  # noqa: E402

from puzzle_generators.helpers.grid import is_well_formed  # noqa: E402

# Rule-source normalization (strip comments, dict literals, for shorthand,
# rule! peel, h/w preamble). Owned by puzzle_generators.rule_wrap so the
# compactor verifier and ad-hoc tooling can import the same pipeline
# without dragging in the rest of the runner.
from puzzle_generators.rule_wrap import wrap_rule  # noqa: E402,F401

SOLUTIONS_DIR = ROOT / "data" / "base" / "solutions"
CANONICAL_PUZZLES = ROOT / "data" / "canonical" / "puzzles.jsonl"
REJECT_DIR = ROOT / "data" / "generated" / ".rejected"
GENERIC_CONCEPTS_DIR = ROOT / "puzzle_generators" / "generic" / "concepts"

# Lazily-built {task_id: program_solution} index over canonical/puzzles.jsonl.
# Used as the LAST rule-resolution fallback so a bundle that ships only the
# generators + canonical puzzles (no data/base/solutions, no full grounded set)
# can still derive outputs for every task. Built once, then reused.
_CANON_RULES: dict | None = None


def _canonical_rule(task_id: str) -> str | None:
    global _CANON_RULES
    if _CANON_RULES is None:
        idx: dict = {}
        if CANONICAL_PUZZLES.exists():
            with open(CANONICAL_PUZZLES) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    code = r.get("program_solution")
                    tid = r.get("task_id") or r.get("content_hash")
                    if tid and code:
                        idx[tid] = code
        _CANON_RULES = idx
    return _CANON_RULES.get(task_id)


def _parens_balanced(code: str) -> bool:
    """Quick balance check for Racket source. Handles () [] plus line
    comments and string literals. Conservative: false if anything is
    suspicious.

    Inlined from scripts/comment_solutions.py so the runner has no
    dependency on the scripts package — this matters when the bundle
    is shipped without the full repo."""
    depth = 0
    i, n = 0, len(code)
    while i < n:
        c = code[i]
        if c == ";":
            while i < n and code[i] != "\n":
                i += 1
            continue
        if c == '"':
            i += 1
            while i < n and code[i] != '"':
                i += 2 if code[i] == "\\" else 1
            i = min(i + 1, n)
            continue
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


def _generic_generator_path(task_id: str) -> Path | None:
    """Resolve ``generic_<family>_genN`` to its concept module path."""
    if not task_id.startswith("generic_"):
        return None
    family, separator, generator = task_id[len("generic_"):].rpartition("_")
    if not separator or not family or not generator.startswith("gen"):
        raise ValueError(
            "generic task id must look like generic_<family>_genN: "
            f"{task_id}"
        )
    path = GENERIC_CONCEPTS_DIR / family / f"{generator}.py"
    if not path.is_file():
        raise FileNotFoundError(f"generic generator not found: {path}")
    return path


def _load_rule(task_id: str) -> tuple[str, str]:
    """Find a usable rule for `task_id` and return (rule_source, source_label).

    Resolution order:
      1. `data/base/solutions/banks/.../*.json` (preferred — gives a
         file path label and supports augmented-variant overrides).
      2. `solvers.grounded_rules.GROUNDED_RULES[task_id]` (fallback —
         used when the rule-source data dir is absent, e.g. a stripped
         review bundle that only ships generators + grounded_rules).

    Multiple JSON solution files can exist for one task_id (training +
    augmented variants). We pick the first one with a non-empty,
    paren-balanced racket_target."""
    generic_path = _generic_generator_path(task_id)
    if generic_path is not None:
        module = _load_generator_module(task_id)
        source = getattr(module, "PROGRAM", None)
        if not isinstance(source, str) or not source.strip():
            raise FileNotFoundError(
                f"generic generator {task_id} has no non-empty PROGRAM"
            )
        source = source.strip()
        if not _parens_balanced(source):
            raise ValueError(f"generic generator {task_id} has unbalanced PROGRAM")
        return source, f"{generic_path.relative_to(ROOT)}:PROGRAM"

    if SOLUTIONS_DIR.exists():
        for f in sorted(SOLUTIONS_DIR.rglob("*.json")):
            try:
                d = json.loads(f.read_text())
            except Exception:
                continue
            if d.get("task_id") != task_id:
                continue
            rt = d.get("racket_target") or {}
            if rt.get("needs_conversion"):
                continue
            src = rt.get("target_code") or rt.get("raw_code") or ""
            src = src.strip()
            if not src or not _parens_balanced(src):
                continue
            return src, str(f.relative_to(ROOT))
    # Fallback: solvers/grounded_rules.py.
    try:
        from solvers.grounded_rules import GROUNDED_RULES
    except Exception:
        GROUNDED_RULES = {}
    rule = GROUNDED_RULES.get(task_id)
    if rule:
        rule = rule.strip()
        if rule and _parens_balanced(rule):
            return rule, "solvers.grounded_rules"
    # Final fallback: the canonical puzzles.jsonl program_solution (covers every
    # task_id, so a stripped bundle without data/base/solutions still works).
    canon = _canonical_rule(task_id)
    if canon:
        canon = canon.strip()
        if canon and _parens_balanced(canon):
            return canon, "data/canonical/puzzles.jsonl"
    raise FileNotFoundError(
        f"no usable rule found for task_id {task_id} "
        f"(checked data/base/solutions/, solvers/grounded_rules.py, "
        f"and data/canonical/puzzles.jsonl)")


# ---------------------------------------------------------------------------
# Generator loading
# ---------------------------------------------------------------------------

def _load_generator_module(task_id: str):
    """Import a per-puzzle generator or a generic concept generator."""
    generic_path = _generic_generator_path(task_id)
    if generic_path is not None:
        family, _, generator = task_id[len("generic_"):].rpartition("_")
        full = f"puzzle_generators.generic.concepts.{family}.{generator}"
        try:
            return importlib.import_module(full)
        except ModuleNotFoundError as e:
            raise FileNotFoundError(
                f"no generic generator module for task_id {task_id} "
                f"(expected {generic_path})"
            ) from e
    full = f"puzzle_generators.per_puzzle.{task_id}.generator"
    try:
        return importlib.import_module(full)
    except ModuleNotFoundError as e:
        raise FileNotFoundError(
            f"no generator module for task_id {task_id} "
            f"(expected puzzle_generators/per_puzzle/{task_id}/generator.py)"
        ) from e


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@dataclass
class Rejection:
    """Why an attempt was rejected. The `reason` is a phase-prefixed
    short tag like 'generate.generator_raised', 'execute.rule_raised',
    'validate.duplicate_pair'. `detail` is a small dict of structured
    context — exception class, dims, hash, etc. Keep payloads small;
    these get persisted line-by-line to the rejection log.

    Phase prefixes:
      generate.* — driver called bundle.generator_module.generate(...)
      execute.*  — Racket bridge applied the rule
      validate.* — well-formedness + identity + dedup checks
    """
    seed: int
    sample_index: int
    reason: str
    detail: dict = field(default_factory=dict)


# Mapping from pre-round-4 unprefixed reason strings to their
# phase-prefixed equivalents. Used by `normalize_rejection_row` for
# tolerant reads of legacy `data/generated/.rejected/<id>.jsonl` lines.
_LEGACY_REASON_MAP = {
    "generator_raised":      "generate.generator_raised",
    "input_not_well_formed": "generate.input_not_well_formed",
    "rule_raised":           "execute.rule_raised",
    "output_not_well_formed": "validate.output_not_well_formed",
    "output_equals_input":   "validate.output_equals_input",
    "duplicate_pair":        "validate.duplicate_pair",
}


def normalize_rejection_row(row: dict) -> dict:
    """Tolerant read of a single rejection-log line.

    Pre-round-4 logs had unprefixed `reason` strings and a `detail`
    that was either a string or absent. Round 4 switched to
    phase-prefixed reasons and dict details. Aggregators and
    diagnostic tools should pipe each row through this normalizer so
    they don't need to special-case the schema break.
    """
    reason = row.get("reason", "")
    if "." not in reason:
        reason = _LEGACY_REASON_MAP.get(reason,
                                         f"legacy.{reason}" if reason else "legacy.unknown")
    detail = row.get("detail", {})
    if isinstance(detail, str):
        detail = {"message": detail} if detail else {}
    elif detail is None:
        detail = {}
    return {**row, "reason": reason, "detail": detail}


def _content_hash(grid_pair: dict) -> str:
    """Stable hash of an (input, output) pair for dedup."""
    blob = json.dumps([grid_pair["input"], grid_pair.get("output", [])],
                      ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


def _sampling_metadata(pairs, accepted_indices, *, n_train, requested_start, rejections):
    """Record indices captured by the sampling loop, never regenerate/infer them."""
    if len(pairs) != len(accepted_indices):
        raise ValueError('Accepted pair/index count differs')
    accepted = []
    for index, (pair, sample_index) in enumerate(zip(pairs, accepted_indices)):
        split = 'train' if index < n_train else 'test'
        accepted.append({'split': split, 'pair_index': index if split == 'train' else index - n_train,
            'sample_index': sample_index,
            'input_sha256': hashlib.sha256(json.dumps(pair['input'], separators=(',', ':')).encode()).hexdigest()})
    return {'schema': 'arcpuzzles-pair-sampling-v1', 'requested_start': requested_start,
            'next_sample_index': accepted_indices[-1] + 1 if accepted_indices else requested_start,
            'attempted_pairs': len(pairs) + len(rejections), 'accepted_pairs': accepted,
            'rejections': rejections}


def _validate_pair(inp, out, *, allow_identity_output: bool) -> Optional[str]:
    """Return None if valid, otherwise a phase-prefixed rejection reason.

    Conservative: only reject what's clearly degenerate. A uniform-color
    output is *legitimate* for many rules (`crop-object` returns a
    monochrome rectangle, `extract-largest` likewise) — we don't flag it."""
    if not is_well_formed(inp):
        return "validate.input_not_well_formed"
    if not is_well_formed(out):
        return "validate.output_not_well_formed"
    if not allow_identity_output and inp == out:
        return "validate.output_equals_input"
    return None


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

@dataclass
class GeneratorBundle:
    """What the runner loads once per batch. Reused across all instances.

    ``task_id`` identifies the generator. ``rule_task_id`` identifies the
    separately reviewed rule authority. They are equal for ordinary families;
    an independent construction family may explicitly reuse a canonical rule by
    declaring ``RULE_TASK_ID`` in its generator module.
    """
    task_id: str
    rule_task_id: str
    rule_source: str
    rule_callable_text: str            # the (lambda (g) ...) string
    rule_file: str
    generator_module: Any
    allow_identity_output: bool = False
    kind: str = "per_puzzle"


def _resolve_rule_task_id(task_id: str, mod: Any, *, kind: str) -> str:
    declared = getattr(mod, "RULE_TASK_ID", task_id)
    if not isinstance(declared, str) or not declared.strip():
        raise ValueError(f"generator {task_id} has invalid RULE_TASK_ID {declared!r}")
    declared = declared.strip()
    if kind == "generic":
        if declared != task_id:
            raise ValueError("generic generators may not alias an external rule authority")
        # A generic id names its own embedded program, not a repository rule
        # authority, so the hex-id charset contract below does not apply to it.
        return declared
    if any(ch not in "0123456789abcdef_" for ch in declared.lower()):
        raise ValueError(
            f"generator {task_id} has unsafe RULE_TASK_ID {declared!r}; "
            "expected a repository task identifier"
        )
    return declared


def _load_bundle(task_id: str) -> GeneratorBundle:
    mod = _load_generator_module(task_id)
    kind = "generic" if _generic_generator_path(task_id) else "per_puzzle"
    rule_task_id = _resolve_rule_task_id(task_id, mod, kind=kind)
    rule_src, rule_file = _load_rule(rule_task_id)
    callable_text = wrap_rule(rule_src)
    # Check for opt-in identity flag in meta.yaml (lightweight: read .meta_allows_identity)
    allow_id = bool(getattr(mod, "ALLOW_IDENTITY_OUTPUT", False))
    return GeneratorBundle(
        task_id=task_id,
        rule_task_id=rule_task_id,
        rule_source=rule_src,
        rule_callable_text=callable_text,
        rule_file=rule_file,
        generator_module=mod,
        allow_identity_output=allow_id,
        kind=kind,
    )


def _open_bridge_with_rule(rule_callable_text: str) -> tuple[RacketBridge, str]:
    """Spin a bridge and pre-define the rule as a named function.
    Returns (bridge, function_name) — caller invokes via
    `(<function_name> <input>)`."""
    b = RacketBridge()
    fn_name = "__pg_rule"
    b.eval_text(f"(define {fn_name} {rule_callable_text})")
    return b, fn_name


def _apply_rule(bridge: RacketBridge, fn_name: str, input_grid) -> list:
    """Define the input grid and call the rule. Returns the output grid."""
    bridge.define_grid("__pg_input", input_grid)
    return bridge.eval_text(f"({fn_name} __pg_input)")


def run_one(
    task_id: str,
    seed: int,
    sample_index: int,
    *,
    n_train: int = 4,
    n_test: int = 1,
    bundle: Optional[GeneratorBundle] = None,
    bridge: Optional[RacketBridge] = None,
    fn_name: Optional[str] = None,
    **axes,
) -> dict:
    """Build one puzzle instance: n_train + n_test (input, output) pairs.

    All pairs in the instance share a seed root and use sequential
    sample_indices starting from `sample_index`."""
    bundle = bundle or _load_bundle(task_id)
    owns_bridge = bridge is None       # if WE opened it, WE must close it (don't leak)
    if bridge is None:
        bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)

    def _close():
        if owns_bridge:
            try:
                bridge.shutdown()
            except Exception:
                pass

    if bundle.kind == "generic":
        try:
            generate_task = getattr(bundle.generator_module, "generate_task", None)
            if not callable(generate_task):
                raise TypeError("generic generator is missing generate_task")
            difficulty = axes.pop("difficulty", "medium")
            if axes:
                raise TypeError(
                    "unsupported generic generator arguments: "
                    + ", ".join(sorted(axes))
                )
            task = generate_task(seed, difficulty=difficulty)
            self_check = getattr(bundle.generator_module, "self_check_task", None)
            if callable(self_check):
                findings = list(self_check(task) or [])
                if findings:
                    raise ValueError(
                        "generic self_check_task failed: " + "; ".join(findings[:3])
                    )
            train = list(task.get("train") or [])
            test = list(task.get("test") or [])
            if not train or not test:
                raise ValueError("generic task must contain train and test pairs")
            seen_hashes: set[str] = set()
            for split_name, pairs in (("train", train), ("test", test)):
                for pair_index, pair in enumerate(pairs):
                    inp, stored = pair.get("input"), pair.get("output")
                    if not is_well_formed(inp) or not is_well_formed(stored):
                        raise ValueError(
                            f"generic {split_name}[{pair_index}] has malformed grids"
                        )
                    actual = _apply_rule(bridge, fn_name, inp)
                    reason = _validate_pair(
                        inp, actual,
                        allow_identity_output=bundle.allow_identity_output,
                    )
                    if reason:
                        raise ValueError(
                            f"generic {split_name}[{pair_index}] failed {reason}"
                        )
                    if actual != stored:
                        raise ValueError(
                            f"generic {split_name}[{pair_index}] stored output "
                            "disagrees with PROGRAM"
                        )
                    content_hash = _content_hash(pair)
                    if content_hash in seen_hashes:
                        raise ValueError(
                            f"generic {split_name}[{pair_index}] duplicates a pair"
                        )
                    seen_hashes.add(content_hash)
            return {
                "task_id": task_id,
                "rule_task_id": bundle.rule_task_id,
                "rule_file": bundle.rule_file,
                "seed": seed,
                "sample_index": sample_index,
                "generator_version": getattr(bundle.generator_module, "VERSION", "?"),
                "train": train,
                "test": test,
            }
        finally:
            _close()

    rejections: list[Rejection] = []
    pairs: list[dict] = []
    accepted_indices: list[int] = []
    seen_hashes: set[str] = set()
    si = sample_index
    needed = n_train + n_test
    max_attempts = needed * 5  # 5x slack before giving up
    attempts = 0
    while len(pairs) < needed and attempts < max_attempts:
        attempts += 1
        try:
            inp = bundle.generator_module.generate(
                seed=seed, sample_index=si, **axes)
        except Exception as e:
            rejections.append(Rejection(seed, si, "generate.generator_raised",
                                         {"exception_class": type(e).__name__,
                                          "message": str(e)[:200]}))
            si += 1
            continue
        if not is_well_formed(inp):
            rejections.append(Rejection(seed, si, "generate.input_not_well_formed",
                                         {"rows": len(inp),
                                          "cols": len(inp[0]) if inp else 0}))
            si += 1
            continue
        try:
            out = _apply_rule(bridge, fn_name, inp)
        except RacketBridgeError as e:
            rejections.append(Rejection(seed, si, "execute.rule_raised",
                                         {"message": str(e)[:200]}))
            si += 1
            continue
        reason = _validate_pair(inp, out,
                                 allow_identity_output=bundle.allow_identity_output)
        if reason:
            rejections.append(Rejection(seed, si, reason, {}))
            si += 1
            continue
        pair = {"input": inp, "output": out}
        h = _content_hash(pair)
        if h in seen_hashes:
            rejections.append(Rejection(seed, si, "validate.duplicate_pair",
                                         {"content_hash": h}))
            si += 1
            continue
        seen_hashes.add(h)
        accepted_indices.append(si)
        pairs.append(pair)
        si += 1

    if len(pairs) < needed:
        # Persistent under-production — write the rejection log so the
        # generator's flaws are visible.
        _record_rejections(task_id, seed, rejections)
        _close()
        raise RuntimeError(
            f"run_one({task_id}, seed={seed}): only produced "
            f"{len(pairs)}/{needed} valid pairs after {attempts} attempts. "
            f"See {REJECT_DIR}/{task_id}.jsonl")

    _close()
    return {
        "task_id": task_id,
        "rule_task_id": bundle.rule_task_id,
        "rule_file": bundle.rule_file,
        "seed":    seed,
        "sample_index": sample_index,
        "generator_version": getattr(bundle.generator_module, "VERSION", "?"),
        "sampling": _sampling_metadata(pairs, accepted_indices, n_train=n_train, requested_start=sample_index,
            rejections=[{"sample_index": r.sample_index, "reason": r.reason, "detail": r.detail} for r in rejections]),
        "train":   pairs[:n_train],
        "test":    pairs[n_train:],
    }


def run_batch(
    task_id: str,
    n: int,
    *,
    n_train: int = 4,
    n_test: int = 1,
    seed_start: int = 0,
    **axes,
) -> list[dict]:
    """Build n independent puzzle instances. Each gets its own seed."""
    bundle = _load_bundle(task_id)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    out = []
    try:
        for i in range(n):
            inst = run_one(
                task_id,
                seed=seed_start + i,
                sample_index=0,
                n_train=n_train, n_test=n_test,
                bundle=bundle, bridge=bridge, fn_name=fn_name,
                **axes,
            )
            out.append(inst)
    finally:
        bridge.shutdown()
    return out


def _record_rejections(task_id: str, seed: int, rejections: Iterable[Rejection]) -> None:
    REJECT_DIR.mkdir(parents=True, exist_ok=True)
    p = REJECT_DIR / f"{task_id}.jsonl"
    with p.open("a") as f:
        for r in rejections:
            f.write(json.dumps({
                "task_id": task_id, "seed": r.seed,
                "sample_index": r.sample_index,
                "reason": r.reason, "detail": r.detail,
            }, ensure_ascii=False) + "\n")
