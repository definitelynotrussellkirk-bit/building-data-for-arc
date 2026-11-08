#!/usr/bin/env python3
"""DSL v2 tokenizer — represent EVERY program with a SMALL core + a default escape.

The v1 vocab was 3,479 tokens and still 97.4% coverage (integer literals + rare heads fell to
OOV). v2 fixes both at once: a small CORE of high-frequency atomic tokens, and a DEFAULT
decomposition escape that *spells out* anything rare, so:

  - coverage is 100% (no token is ever un-representable -> no OOV), and
  - the vocab is far SMALLER than v1.

Encoding of one program atom:
  ( ) [ ]                         -> itself
  integer  e.g. -1, 999999        -> <int> <neg>? d i g i t s </int>   (any magnitude, ~few tokens)
  float    e.g. 0.33              -> <float>
  #t #f                           -> itself (atomic)
  'sym     e.g. 'left             -> <sym> c h a r s </esc>
  #:kw     e.g. #:when            -> <kw>  c h a r s </esc>
  "str"    e.g. "lr"              -> <str> c h a r s </esc>
  head/var in CORE                -> the atomic token
  head/var NOT in core            -> <id>  c h a r s </esc>          (the default way)

`to_tokens` is total (never raises, never drops); `from_tokens` is its inverse so a decoded
program can be run through the Racket verifier. Coverage/size are auditable via __main__.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEAD_FREQ = ROOT / "data/derived/head_frequency.jsonl"

# ---- the closed STRUCTURAL pieces (small, fixed) ----------------------------
CONTROL = ["<synth>", "<predict>", "<exec>", "<repair>", "<invert>"]
# <invert>: demos + the OUTPUT grid -> predict a VALID input grid (reverse task; need not be unique,
# validity = running the predicted input through the gold program reproduces the output).
GRID = ["<grid>", "</grid>", "<row>", "</row>", "<io>"]
STRUCT = ["(", ")", "[", "]"]
SPECIAL = ["<pad>", "<bos>", "<sep>", "<eos>"]
MARK = ["<id>", "<sym>", "<kw>", "<str>", "<esc>", "<int>", "<neg>", "<float>", "#t", "#f"]
# LATENT SCRATCHPAD — an optional, UNGRADED, size-capped region the model may use before the
# answer. <think>..</think> bracket it; LATENT is a private "latent vocab" (z0..zK) the model
# can compose freely in that region. We never supervise it (loss-masked): it just EXISTS — if
# the model finds it useful (via the answer-loss gradient / verifier reward at RL/TTT) it uses
# it, otherwise it ignores it. The trainer caps how many latent positions a sample may hold.
N_LATENT = 64
THINK = ["<think>", "</think>"] + [f"<z{i}>" for i in range(N_LATENT)]
DIGITS = [str(d) for d in range(10)]
# every char that can appear inside a Racket head / symbol / keyword / string we spell.
# letters + digits + the head symbol set + a few string/keyword chars. Verified vs corpus in __main__.
ALPHA = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") + \
        list("!*+<>=?/.-_:%&^~@$',;") + [" "]   # digits+punct appear INSIDE spelled names/strings
CHAR_TOKENS = [f"§{c}" for c in ALPHA]        # char tokens are prefixed so they never collide
SPECIAL_FORMS = [
    "lambda", "define", "let", "let*", "letrec", "if", "cond", "else", "begin",
    "and", "or", "not", "when", "unless", "case", "quote",
    "for", "for/list", "for/sum", "for/fold", "for/or", "for/and", "for/first",
    "for*", "for*/list", "for*/fold", "rule!",
]

# `{`/`}` are the DSL's dict-literal (recolor-table) delimiters — `{K V K V ...}` is rewritten to
# `(make-immutable-hash (list (cons K V) ...))` by puzzle_generators.rule_wrap.convert_dict_literals
# before the bridge sees it, so they are REAL structure, not noise. They used to be excluded from the
# atom class with NO alternative production, so `finditer` silently SKIPPED them and
# `(casev n {1 1 2 2} 0)` detokenized as `(casev n 1 1 2 2 0)` — a different program (gold
# fa3e0c305476). They are now first-class structural atoms. (reviewer kimi3 §2.1)
_ATOM = re.compile(r"\(|\)|\[|\]|\{|\}|\"[^\"]*\"|[^\s()\[\]{}]+")
STRUCT_ATOMS = ("(", ")", "[", "]", "{", "}")
_INT = re.compile(r"-?\d+")
# Exponent form included: gold uses `1e18` as a "+infinity" sentinel (task 474634a9f7b7). Without the
# `[eE]` alternative it tokenized as an <id> — i.e. as a VARIABLE named `1e18`, which the new
# argument-position scope check correctly refused. It is a number, so lex it as one.
_FLOAT = re.compile(r"-?\d+\.\d+(?:[eE][-+]?\d+)?|-?\d+[eE][-+]?\d+")


VOCAB_JSON = ROOT / "data/derived/dsl_vocab.json"
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"   # next252: exported for dsl_grammar's validator
PRELUDE = ROOT / "arc_repl/racket_prelude/arc-prelude.rkt"
# Racket builtins the corpus calls that aren't prelude-defined (extend as the audit finds more).
RACKET_BUILTINS = [
    "zero?", "argmin", "argmax", "add1", "sub1", "expt", "gcd", "lcm", "abs",
    "set", "set-add", "set-member?", "set-remove", "set-union", "set->list", "list->set",
    "hash", "hash-ref", "hash-set", "hash-has-key?", "make-hash", "hash-keys", "hash-values",
    "char->integer", "integer->char", "exact-round", "exact-floor", "exact-ceiling",
    "remainder", "modulo", "quotient", "even?", "odd?", "positive?", "negative?",
]

# The default v2 table is a checkpoint ABI, not a live reflection of every prelude definition.
# These seven prelude-only names were atomic in the inherited 4,696-row layout. Later prelude
# helpers remain fully callable through runtime_callables(), but are encoded losslessly through
# the existing <id> character-spelling path instead of silently inserting embedding rows.
CHECKPOINT_STABLE_PRELUDE_ATOMIC_HEADS = frozenset({
    "build-grid", "build-like", "build-shape", "cellmap",
    "with-bbox", "with-shape", "with-shape*",
})
CHECKPOINT_V2_VOCAB_SIZE = 4696
CHECKPOINT_V2_NONRESERVED_SHA256 = (
    "b161f27c09a08ac1faf6548a51ac1012fa3c7129b340a72c730ba875fe6e4710"
)


def prelude_callables() -> set[str]:
    """All callable names defined in the prelude: `(define (f ...))`, `(define f ...)`, AND
    `(define-syntax[-rule] (m ...))` macros (cellmap/build-grid/with-bbox/... that the plain
    define-regex missed — Reviewer 2's 'head extraction not runtime-aware')."""
    if not PRELUDE.exists():
        return set()
    text = PRELUDE.read_text(errors="replace")
    out = set()
    for m in re.finditer(r"\(define(?:-syntax(?:-rule)?)?\s+\(?\s*([a-zA-Z][a-zA-Z0-9!*+<>=?/.-]*)", text):
        out.add(m.group(1))
    return out


# Runtime-callable names valid in operator position but NOT worth an atomic vocab head (they'd force a
# checkpoint-incompatible vocab resize). They appear in gold programs and are emitted through the <id>
# spelling path; the constrained grammar admits them via runtime_callables() so gold stays admissible
# without growing the 4696-token table (reviewer next357 — fixed operator-position <id> false-rejects).
EXTRA_RUNTIME_CALLABLES = {
    "findf", "filter-map", "flatten", "remove", "assoc", "member", "pair?",
    "car", "cdr", "caar", "cadr", "cdar", "cddr", "atan",
    "mutable-set", "list->mutable-set", "set-add!", "set-for-each", "set-remove!",
    "hash-set!", "hash-remove", "hash-copy", "hash-remove!", "hash-count",
    "make-vector", "vector", "vector-ref", "vector-set!", "vector-length",
    "void", "string<?", "string>?", "string=?", "string<=?", "string>=?",
    "for/set", "for/hash", "for/product", "for/max", "for/min",
    "for*/sum", "for*/or", "for*/and", "for*/first",
    "andmap", "ormap", "foldl", "foldr", "take", "drop", "memf",
    "append*", "build-vector", "list->vector", "vector->list", "replace",
    # layer-* helpers present in gold programs but not in the atomic core vocab
    "layer-flip",
    # `number?` is passed as a VALUE in gold (`(filter number? ...)`, 20 rows). The operator-position
    # inventory in grammar_gate.py never saw it because it is never a head; the new argument-position
    # scope check (kimi3 §1.2) does. A real Racket predicate belongs in the callable universe.
    "number?",
}


def runtime_callables() -> set[str]:
    """Every name the constrained grammar accepts in operator position: atomic Racket builtins,
    the rare EXTRA_RUNTIME_CALLABLES helpers, and all prelude defines/macros. Spelled via <id> when
    not an atomic head, so admitting them fixes false grammar rejects without resizing the vocab."""
    return set(RACKET_BUILTINS) | EXTRA_RUNTIME_CALLABLES | prelude_callables()


def core_heads(n: int) -> list[str]:
    """Atomic head tokens.

    n<=0 (default) preserves the checkpointed v2 ABI: dsl_vocab.json heads, the explicitly
    checkpointed prelude-only subset, and Racket builtins. Every other prelude definition remains
    grammar-admissible via runtime_callables() and is encoded through lossless <id> spelling.
    n>0 selects top-n frequent heads for intentionally smaller ablations only.
    """
    if n <= 0:
        if not VOCAB_JSON.exists():         # LOUD: a missing asset -> incomplete vocab -> broken model
            print(f"LOUD: dsl_vocab.json MISSING at {VOCAB_JSON} — head vocab will be INCOMPLETE "
                  f"(checkpoint-stable prelude heads+builtins only). Fix the asset path before "
                  f"training/eval.", file=sys.stderr)
        base = set(json.load(VOCAB_JSON.open()).get("heads", [])) if VOCAB_JSON.exists() else set()
        return sorted(base | CHECKPOINT_STABLE_PRELUDE_ATOMIC_HEADS | set(RACKET_BUILTINS))
    if not HEAD_FREQ.exists():
        return []
    rows = []
    for line in HEAD_FREQ.open():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(r.get("head"), str):
            rows.append((int(r.get("count", 0)), r["head"]))
    rows.sort(reverse=True)
    return [h for _, h in rows[:n]] if n > 0 else [h for _, h in rows]


# RESERVED — spare vocab slots at the TAIL of the vocab. Unused by default (cost = one tied
# embedding row each, ~negligible). Two uses: (a) FREE LATENT registers the model may compose in
# the <think> region (extra scratchpad capacity), and (b) CLAIM-LATER slots for future tokens (new
# control mode, structural token, etc.) — rename a <rsv_i> in place and its index never moves, so
# the embedding table never resizes and existing checkpoints stay load-compatible. Tail placement
# is what guarantees claiming never shifts any other token's id.
N_RESERVED = 1024    # huge on purpose: ~0.5% params @0.2B / 0.26% @0.5B (tied emb) — a big pool of
# CLAIMED reserved slots for the FACT-SCRATCHPAD (renamed IN PLACE at the head of the reserved block:
# vocab SIZE is unchanged, so existing checkpoints load fine — the slots were untrained rsv rows).
#   <facts>..</facts>  bracket a FED deterministic grounding preamble (auto_scan/suggest ->
#                      "PROPERTY <rating 0-99>" pairs) the model READS before answering.
#   <pred_facts>       task tag: demos -> the property ratings (the ~10% perception aux task).
#   <p_*>              one token per auto_scan feature / suggest template; rating = 2 DIGITS after it.
FACTS_CTRL = ["<facts>", "</facts>", "<pred_facts>"]
FACTS_PROPS = [
    "<p_consistent_map>", "<p_color_roles>", "<p_frames>", "<p_lines>", "<p_regularity>",
    "<p_motion>", "<p_scattered>", "<p_shape_change>", "<p_diff>", "<p_change_type>",
    "<p_objcount>", "<p_enclosure>", "<p_lattice>", "<p_symmetry>", "<p_periodicity>",
    "<p_recolor_map>", "<p_fill_enclosed>", "<p_complete_sym>", "<p_upscale>", "<p_recolor_single>",
]
FACTS_TOKENS = FACTS_CTRL + FACTS_PROPS
# <trace>..</trace> wrap a <repair> FAILURE TRACE: the broken program's ACTUAL (wrong) output grid,
# so repair learns from the concrete failure (executed in the hindsight gen), not a blind corruption.
REPAIR_CTRL = ["<trace>", "</trace>"]
# <equiv> A <vs> B <io> input -> DIGITS: how many cells A and B differ by on this input (0..900).
# Teaches program-semantics / equivalence reasoning (sometimes identical, sometimes divergent).
EQUIV_CTRL = ["<equiv>", "<vs>"]
# <judge> demos <io> candidate-program -> 2 DIGITS (00-99): predicted fraction of the demos the
# program reproduces. The model-as-value-head (task #40): labels come FREE from the repair-trace
# miner (it executes every candidate), and at pass@2 time candidates are ranked by the judged
# score. Claimed in place of a reserved slot -> vocab size/ids unchanged, checkpoints load fine.
JUDGE_CTRL = ["<judge>"]
# <errmask> demos <io> input <io> a (wrong) prediction -> a FULL 30x30 HOT MASK: 1 where the
# prediction differs from truth (the mistake cells, incl. size mismatch), else 0. A cell-error
# self-critic — the model learns to predict WHERE it errs WITHOUT seeing truth, so the
# verify->repair loop can focus on flagged cells. Claimed in place of a reserved slot -> vocab
# size/ids unchanged, checkpoints load fine.
ERRMASK_CTRL = ["<errmask>"]
# `{` `}` — the dict-literal delimiters (see _ATOM above). They belong logically in STRUCT, but STRUCT
# sits BEFORE the head table, so putting them there would shift every later token id and break every
# existing checkpoint. Claiming two reserved slots instead is the documented mechanism: vocab SIZE is
# unchanged (RESERVED still totals N_RESERVED) and no non-reserved id moves. (reviewer kimi3 §2.1)
BRACE_STRUCT = ["{", "}"]
CLAIMED = FACTS_TOKENS + REPAIR_CTRL + EQUIV_CTRL + JUDGE_CTRL + ERRMASK_CTRL + BRACE_STRUCT
RESERVED = CLAIMED + [f"<rsv{i}>" for i in range(N_RESERVED - len(CLAIMED))]  # total still 1024


def default_vocab_nonreserved_sha256(tokens: list[str]) -> str:
    """Fingerprint the checkpoint-stable prefix while permitting reserved-tail claims."""
    if len(tokens) < N_RESERVED:
        raise ValueError(f"vocab has {len(tokens)} rows, fewer than N_RESERVED={N_RESERVED}")
    payload = ("\n".join(tokens[:-N_RESERVED]) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _assert_default_vocab_checkpoint_layout(tokens: list[str]) -> None:
    actual_hash = default_vocab_nonreserved_sha256(tokens)
    if len(tokens) == CHECKPOINT_V2_VOCAB_SIZE and actual_hash == CHECKPOINT_V2_NONRESERVED_SHA256:
        return
    raise RuntimeError(
        "LOUD: default DSL-v2 vocabulary layout drifted from the checkpoint ABI: "
        f"size={len(tokens)} (expected {CHECKPOINT_V2_VOCAB_SIZE}), "
        f"nonreserved_sha256={actual_hash} "
        f"(expected {CHECKPOINT_V2_NONRESERVED_SHA256}). "
        "Do not add prelude definitions to the atomic table implicitly. Keep new callables on the "
        "<id> spelling path, claim a reserved tail slot, or perform an explicit checkpoint migration."
    )


def build_core_vocab(n_heads: int = 0) -> tuple[list[str], set[str]]:
    """Return (token_list, atomic_head_set). Everything not in the head set is spelled.

    The default table is checkpoint-stable. Positive n_heads values are explicit smaller-vocab
    ablations and therefore intentionally bypass the default-layout ABI guard.
    """
    heads = core_heads(n_heads)
    toks = list(dict.fromkeys(
        SPECIAL + CONTROL + GRID + STRUCT + MARK + THINK + DIGITS + CHAR_TOKENS
        + SPECIAL_FORMS + heads + RESERVED))     # RESERVED last -> claiming never shifts an id
    if n_heads <= 0:
        _assert_default_vocab_checkpoint_layout(toks)
    return toks, set(heads) | set(SPECIAL_FORMS)


def _spell(s: str) -> list[str]:
    return [f"§{c}" for c in s]


def _unspell(chars: list[str]) -> str:
    return "".join(c[1:] for c in chars)   # drop the § prefix


def grid_to_tokens(grid) -> list[str]:
    out = ["<grid>"]
    for row in grid:
        out.append("<row>")
        out += [str(int(c)) for c in row]
        out.append("</row>")
    out.append("</grid>")
    return out


def io_example_tokens(inp, out) -> list[str]:
    return ["<io>"] + grid_to_tokens(inp) + grid_to_tokens(out)


def strip_line_comments(program: str) -> str:
    """Remove Racket `;` line comments outside strings before tokenization.

    from_tokens emits a whitespace-normalized ONE-LINE program; if `;; comment` tokens survive,
    the collapsed newline lets the comment swallow the rest of the decoded program. Comments
    aren't training targets, so strip them (respecting quoted strings). (reviewer next252 fix)
    """
    out = []
    in_str = False
    i, n = 0, len(program)
    while i < n:
        ch = program[i]
        if in_str:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(program[i + 1]); i += 2; continue
            if ch == '"':
                in_str = False
            i += 1; continue
        if ch == '"':
            in_str = True; out.append(ch); i += 1; continue
        if ch == ";":
            while i < n and program[i] != "\n":   # skip to end of line
                i += 1
            continue
        out.append(ch); i += 1
    return "".join(out)


def to_tokens(program: str, core: set[str]) -> list[str]:
    """Total, lossless tokenization over the v2 vocab. 100% coverage by construction.

    LOUD on any character `_ATOM` cannot match: the module contract (top of file) is
    "never drops". A silently skipped character re-corrupts a program the way `{`/`}` did
    (kimi3 §2.1) and the token-level roundtrip audit CANNOT see it, because both directions
    drop identically. Anything unmatched is reported to stderr with its position + context.
    """
    program = strip_line_comments(program)   # next252: ;; comments corrupt the one-line decode
    out: list[str] = []
    last_end = 0
    dropped: list[tuple[int, str]] = []
    for m in _ATOM.finditer(program):
        gap = program[last_end:m.start()]
        if gap.strip():                       # non-whitespace the regex refused to consume
            dropped.append((last_end, gap.strip()))
        last_end = m.end()
        a = m.group(0)
        if a in STRUCT_ATOMS:
            out.append(a)
        elif a in ("#t", "#f"):
            out.append(a)
        elif _FLOAT.fullmatch(a):
            out += ["<float>", *_spell(a), "<esc>"]   # spell exactly (0.6 != 0.0)
        elif _INT.fullmatch(a):
            out.append("<int>")
            if a.startswith("-"):
                out.append("<neg>"); a = a[1:]
            out += list(a)            # digits are atomic tokens 0-9
            out.append("<esc>")
        elif a.startswith('"') and a.endswith('"') and len(a) >= 2:
            out += ["<str>", *_spell(a[1:-1]), "<esc>"]
        elif a.startswith("'"):
            out += ["<sym>", *_spell(a[1:]), "<esc>"]
        elif a.startswith("#:"):
            out += ["<kw>", *_spell(a[2:]), "<esc>"]
        elif a in core:
            out.append(a)
        else:
            out += ["<id>", *_spell(a), "<esc>"]
    tail = program[last_end:]
    if tail.strip():
        dropped.append((last_end, tail.strip()))
    if dropped:
        where = ", ".join(f"@{i}:{s[:20]!r}" for i, s in dropped[:5])
        print(f"LOUD: to_tokens DROPPED {len(dropped)} unmatched char run(s) — {where} "
              f"(program starts {program[:60]!r}). The token stream is NOT a faithful encoding; "
              f"extend _ATOM before training/eval on it.", file=sys.stderr)
    return out


def from_tokens(toks: list[str]) -> str:
    """Inverse of to_tokens -> a runnable Racket program string."""
    out: list[str] = []
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        if t in ("(", "[", "{"):
            out.append(t); i += 1; continue
        if t in (")", "]", "}"):
            if out and out[-1] == " ":
                out.pop()
            out.append(t); i += 1
            out.append(" "); continue
        if t == "<int>":
            i += 1; neg = ""
            if i < n and toks[i] == "<neg>":
                neg = "-"; i += 1
            ds = []
            while i < n and toks[i].isdigit():
                ds.append(toks[i]); i += 1
            if i < n and toks[i] == "<esc>":
                i += 1
            out.append((neg + "".join(ds)) if ds else "0")   # fail-close: empty/sign-only int -> "0"
            out.append(" "); continue
        if t in ("<id>", "<sym>", "<kw>", "<str>", "<float>"):
            kind = t; i += 1
            chars = []
            while i < n and toks[i].startswith("§"):
                chars.append(toks[i]); i += 1
            if i < n and toks[i] == "<esc>":
                i += 1
            s = _unspell(chars)
            pre = {"<id>": "", "<sym>": "'", "<kw>": "#:", "<str>": '"', "<float>": ""}[kind]
            suf = '"' if kind == "<str>" else ""
            out.append(pre + s + suf); out.append(" "); continue
        # atomic head / special form / #t / #f
        out.append(t); out.append(" "); i += 1
    s = "".join(out)
    return re.sub(r"\s+([)\]}])", r"\1", re.sub(r"([(\[{])\s+", r"\1", s)).strip()


if __name__ == "__main__":  # coverage + size + roundtrip audit
    import sys
    from collections import Counter
    n_heads = int(sys.argv[1]) if len(sys.argv) > 1 else 256
    toks, core = build_core_vocab(n_heads)
    print(f"v2 vocab size: {len(toks)}  (core heads={n_heads})  vs v1 3479")
    # verify the alphabet covers every char that appears in heads/symbols/strings
    canonical = ROOT / "data/canonical/puzzles.jsonl"
    charset_needed = set()
    lens = []
    bad_roundtrip = 0
    n = 0
    tok_counts = Counter()
    for line in canonical.open():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        p = (r.get("program_solution") or "").strip()
        if not p:
            continue
        n += 1
        t = to_tokens(p, core)
        lens.append(len(t))
        tok_counts.update(t)
        # any token outside the vocab? (would be a coverage hole)
        for x in t:
            if x.startswith("§"):
                charset_needed.add(x)
        # roundtrip: tokens -> program -> tokens must be stable
        if to_tokens(from_tokens(t), core) != t:
            bad_roundtrip += 1
    vocabset = set(toks)
    missing_chars = charset_needed - vocabset
    lens.sort()
    print(f"programs: {n}")
    print(f"coverage: 100% by construction; tokens outside vocab: "
          f"{sum(1 for x in tok_counts if x not in vocabset)} (chars missing: {len(missing_chars)})")
    if missing_chars:
        print("  MISSING CHAR TOKENS (extend ALPHA):", sorted(_unspell([c]) for c in missing_chars))
    print(f"roundtrip stable: {n - bad_roundtrip}/{n}")
    print(f"token-length median={lens[len(lens)//2]} p90={lens[int(len(lens)*.9)]} "
          f"p99={lens[int(len(lens)*.99)]} max={lens[-1]}")
