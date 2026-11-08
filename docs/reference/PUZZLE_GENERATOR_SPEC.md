# Puzzle-Instance Generator Spec

> Contract for `puzzle_generators/per_puzzle/<task_id>/generator.py`.
> Phase 2 of [`PUZZLE_GENERATOR_ROADMAP.md`](PUZZLE_GENERATOR_ROADMAP.md).

A **puzzle-instance generator** produces fresh `(input, output)` pairs
for one ARC puzzle. The output is *derived* — never stored — by piping
the generator's input through that puzzle's already-existing Racket
rule. One source of truth: `output = rule(generate(seed, axes))`.

## Module shape

Every generator module is a Python file at
`puzzle_generators/per_puzzle/<task_id>/generator.py` exporting:

| Symbol           | Type    | Meaning                                                                                                                              |
|------------------|---------|--------------------------------------------------------------------------------------------------------------------------------------|
| `GENERATOR_ID`   | `str`   | Stable identifier. Conventionally equal to `TASK_ID`.                                                                                |
| `VERSION`        | `str`   | Semver (`"1.0.0"`). Bump when output distribution changes; downstream caches key on this.                                            |
| `TASK_ID`        | `str`   | The canonical puzzle this generator produces variants of. Must match a `task_id` in `data/base/solutions/`.                          |
| `CONCEPT_HASH`   | `str` (optional) | The canonical-rule hash from `scripts/concept_inventory.py` (which writes `data/derived/concepts.jsonl` — the same source the field comments cite). Optional as of round-7 audit. Empty string `""` is **worse than absent** (looks filled, conveys nothing) — either fill it or omit the constant. |
| `SUMMARY`        | `str`   | One-sentence description of what the generator builds.                                                                               |
| `INVARIANTS`     | `list[str]` | Constraints the generator guarantees (used by the LLM author and as runtime asserts where cheap).                                |
| `AXES`           | `dict`  | Free axes the caller can override. Keys are kwarg names; values describe type, default, and validity. See **Axes** below.            |
| `generate(...)`  | `callable` | The actual function. See **Function signature** below.                                                                            |

A `meta.yaml` sibling holds free-form notes (invariant rationale, why
certain axes were chosen) that don't need to live in code. Optional —
the runner doesn't read it.

## Function signature

```python
def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides,
) -> list[list[int]]:
    """Build one input grid. Output comes from piping through the rule."""
```

- `seed`, `sample_index`: deterministic identity. Same `(seed,
  sample_index, version)` always produces the same grid.
- `difficulty`: `"easy" | "medium" | "hard" | None`. Optional hint;
  generators may ignore it. When set, narrows axis ranges (e.g., easy
  → smaller grids, fewer objects).
- `**overrides`: per-axis overrides (`bg=5, marker_color=2,
  grid_h=12, …`). Anything in `AXES` is a valid kwarg.
- **Returns** the input grid as `list[list[int]]` with values in
  `0..9`, height/width in `[1, 30]`. The runner derives the output by
  calling the puzzle's Racket rule.

The function MUST NOT compute or return the output. The runner owns
that step. This keeps the rule as the single source of truth.

## Axes

`AXES` is a documented contract for what's tweakable. Each entry:

```python
AXES = {
    "bg": {
        "type": "color",
        "default": "rng",
        "valid": "0..9",
        "doc": "Background color of the grid.",
    },
    "rect_color": {
        "type": "color",
        "default": "rng",
        "valid": "0..9 != bg",
        "doc": "Color of the single rectangle.",
    },
    "grid_h": {
        "type": "int",
        "default": "rng 10..14",
        "valid": "5..30",
        "doc": "Grid height.",
    },
    # ...
}
```

Type vocabulary:

| Type       | Meaning                                                |
|------------|--------------------------------------------------------|
| `color`    | A single integer in `0..9`.                            |
| `colors[N]`| Tuple of N distinct colors.                            |
| `int`      | A single integer.                                      |
| `shape`    | An `(h, w)` pair.                                      |
| `rc`       | An `(row, col)` position.                              |
| `bool`     | True/False knob.                                       |
| `enum`     | One of a fixed set of strings.                         |

`AXES` is the **machine-readable** description the LLM author and the
catalog read. The runner uses it to validate overrides ("rect_color is
declared as `0..9 != bg`, you passed 11 — reject").

### Reserved full-grid dimension axes

The override checker gives geometric meaning to these integer axis names. They
always describe the dimensions of the **full input grid returned by
`generate()`**:

| reserved names | required observed value |
|----------------|-------------------------|
| `grid_h`, `canvas_h`, `height` | `len(returned_grid)` |
| `grid_w`, `canvas_w`, `width` | `len(returned_grid[0])` |
| `grid_size`, `canvas_size` | the full returned square size |

Do not use `grid_h` or `grid_w` for a panel, object, crop, tile, or derived
output dimension. For example, a two-panel input with panel width 5 and a
one-column divider has `grid_w == 11`, not 5. Name the task-local axis
`panel_w`, `object_w`, `tile_w`, or `output_w` as appropriate and report its
realized value from `observe_overrides(grid)`. The same distinction applies to
height axes. This makes an override claim observable without confusing local
geometry with the returned-grid contract.

## GenCtx — the keyed-draw discipline

All randomness goes through `GenCtx` from `puzzle_generators.base`:

```python
from puzzle_generators.base import gen_ctx

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index,
        version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )
    bg          = ctx.draw_color("bg")
    rect_color  = ctx.draw_color("rect_color", exclude={bg})
    grid_h      = ctx.draw_int("grid_h", 10, 14)
    grid_w      = ctx.draw_int("grid_w", 10, 14)
    # ... build and return a grid
```

**Every random decision uses a label.** The label is hashed against
`(seed, version, task_id)` to seed an independent `random.Random`.
This means:

- Adding/removing/reordering draws cannot affect the values of *other*
  draws. Two generators that both call `ctx.draw_color("bg")` get the
  same `bg` for the same seed regardless of what other draws happen.
- Determinism is portable: `(seed=42, sample_index=3)` produces the
  same grid on any machine, any Python version.
- An override (`bg=5` in kwargs) short-circuits the draw and is
  recorded in `ctx.overrides_used` for provenance.

The `GenCtx` API:

| Method                                                | Returns           |
|-------------------------------------------------------|-------------------|
| `draw_int(label, lo, hi)`                             | `int` in `[lo, hi]` |
| `draw_choice(label, options)`                         | one element of `options` |
| `draw_color(label, *, exclude=set())`                 | `int` in `0..9 \ exclude` |
| `draw_distinct_colors(label, n, exclude=set())`       | `tuple[int, ...]` of length n |
| `draw_grid_size(label, lo, hi)`                       | `(h, w)` |
| `draw_rect_size(label, grid, margin, min_dim)`        | `(rh, rw)` fitting inside grid |
| `draw_rect_position(label, grid, size, margin)`       | `(rr, rc)` such that rect fits with margin |
| `draw_rng(label)`                                     | a `random.Random` for ad-hoc draws inside helpers |

If `label` matches a key in `overrides`, the override value is used
verbatim (after passing the same validity check the random draw
applies). The override is recorded and readable via `ctx.overrides_used()`.

### Draw-provenance: the public pinned-axis API (contract v14)

Read provenance ONLY through these methods — never through private
attributes:

| Method                       | Returns                                          |
|------------------------------|--------------------------------------------------|
| `recorded_draws()`           | `{label: value}` copy of every keyed draw so far |
| `axis_value(label, default)` | one recorded value (or default)                  |
| `draw_bounds(label)`         | `(lo, hi)` the label was drawn under, or `None`  |
| `draw_options(label)`        | option tuple for a choice draw, or `None`        |
| `overrides_used()`           | `{label: value}` overrides actually consumed     |

The old private names (`_drawn`, `_draw_bounds`, `_draw_options`,
`_override_used`) remain as deprecated live-view aliases for two review
rounds (a `DeprecationWarning` fires once per process on first access),
then may be removed. A generator that needs to pin a profile-linked axis
should express it as a degenerate keyed draw (`ctx.draw_int(label, v, v)`
or a single-option `draw_choice`) rather than writing into the stores.

## Validation (runner-side)

Every grid the generator returns is validated by the runner before
being included in the batch:

1. **Type:** `list[list[int]]`.
2. **Dimensions:** `1 ≤ h ≤ 30`, `1 ≤ w ≤ 30`, all rows same length.
3. **Values:** every cell in `0..9`.
4. **Non-degenerate input:** at least two distinct colors. (A
   uniform-bg-only grid is almost always a generator bug.)
5. **Rule applies cleanly:** `bridge.eval_text(rule)` returns a grid;
   any error → reject.
6. **Non-degenerate output:** output is not all-bg, and not equal to
   input. (If the rule's purpose is to *not* change the input — rare
   — the generator declares `allow_identity_output: true` in
   `meta.yaml`.)

Rejected instances go to `data/generated/.rejected/<task_id>.jsonl`
with `{seed, sample_index, reason}`. The runner retries up to N times
per requested instance (default N=3) before giving up.

## Defect lint (`scripts/generator_defect_lint.py`) — the canonical-anchored gate

Beyond runner validation, every generator is held to the canonical task
it claims to generate. The defect lint samples instances across
difficulty bands, applies the canonical Racket rule, and checks
(ERROR-level findings gate; WARN-level findings are advisory —
`--strict` elevates them):

1. **Canonical coverage (ERROR)** — the canonical train inputs must be
   IN-DISTRIBUTION for the generator: for area / h / w / n_colors /
   obj_count, the canonical median must fall inside the generated
   sample's envelope; the canonical background (modal) color must be
   producible. A canonical demo the generator can never emit means the
   model trains on a different task than it is scored on.
   (`max_obj` residuals report at WARN as `canonical_coverage_soft`.)
2. **Transformation fingerprint (WARN)** — the rule's EFFECT on
   generated inputs (size relation, colors introduced, changed-cell
   fraction) must match its effect on the canonical demos. Catches
   inputs that look plausible but don't exercise the transformation
   (wrong marker/wall colors, missing trigger structures).
3. **Axis honesty (ERROR/WARN)** — GenCtx records the bounds actually
   passed to `draw_int`/`draw_choice`; drawing outside the declared
   `AXES` `valid` range is an ERROR (the metadata lies), a wide declared
   range that sampling barely taps is a WARN.
4. **Hash-seed determinism (ERROR)** — `generate()` re-run in
   subprocesses under different `PYTHONHASHSEED` values must be
   identical; a difference means set/dict iteration-order dependence
   (the class that poisoned `ffaca7acb482`). Skip in bulk with `--fast`.
5. **self_check power (WARN)** — mutation test: structure-destroying
   mutations (cell shuffle, transpose, block stomp, color swap) of the
   generator's own accepted instances should be REJECTED by its
   `self_check`. Near-zero rejection = palette-only invariant.
6. **Self-calibration** — every per-pair detector first runs on the
   canonical pairs themselves; if it fires there, the property is the
   TASK (solid-label outputs, identity demos by design, …) and the
   detector is disabled for that task instead of hand-exempted.
7. **Rule-staleness pin (ERROR)** — generators may declare
   `RULE_HASH = sha256(" ".join(program_solution.split()))[:12]`, the
   canonical rule's hash at authoring time. Every wrong-task defect in
   the corpus had one root cause: the rule was replaced and the
   generator silently went stale. A mismatched pin errors; beautifying
   a rule means re-verifying its generator and re-pinning. Add the pin
   whenever you author or fix a generator.
8. **Dead difficulty knob (WARN)** — byte-identical instances across
   easy/medium/hard for every sampled seed (the band never entered a
   draw).
9. **Rule performance (WARN)** — slowest rule application > 5s on this
   generator's inputs (a Kaggle/timeout hazard).
10. **Rule-crash + self_check blind spot (WARN)** — rule applications
    that crash are counted, and if `self_check` ACCEPTED the crashing
    inputs the blind spot is named (the safety net misses a real
    failure mode).
11. **Texture-override contract (WARN)** — every declared
    `DEGENERATE_TEXTURES` / `HELPFUL_TEXTURES` name is actually invoked
    via `generate(..., texture=name)`: a crash, an invalid grid, a dead
    branch (byte-identical to the un-textured draw for every seed), or a
    "helpful" texture that fails `self_check` all warn. No other gate
    ever calls these branches.
12. **Rule-source divergence (ERROR/WARN)** — the runner
    (`run_one`/`run_batch`, `lint_generator --validate`, the SFT
    builders) resolves the rule from `data/base/solutions/*.json`, NOT
    canonical. When the two texts differ, severity is decided
    BEHAVIORALLY: the base rule is applied to the sampled inputs —
    different outputs is an ERROR (the wrong-task class: two pipelines
    silently train/validate on different rules), matching outputs is a
    WARN (an unsynced beautification). Corpus inventory:
    `data/derived/rule_source_divergence.json`.

13. **Duplicate inputs (WARN)** — distinct-input rate within each
    difficulty band < 70%: different seeds re-mint the same grids,
    silently shrinking the always-unique stream. (Dedup is per-band:
    the same seed across overlapping bands is legitimately identical —
    that's the dead-bands probe's territory.)

Note on canonical encoding: 609 canonical tasks store grids as
digit-string rows (`"002050"`). `_load_canon` decodes them
(`_decode_grid`) — before 2026-07-02 every canonical-anchored detector
silently skipped those tasks. Any tool comparing grids against
canonical must decode the same way (see `scripts/sync_base_rules.py`).

A companion tool ranks WHERE to widen: `scripts/eval_gap_rank.py`
featurizes the 120 eval tasks and the whole generator corpus
(input-only, bridge-free) and emits per-feature quantile gaps, the
least-covered eval tasks, and the generators nearest each hole
(`data/derived/eval_gap_ranking.json`).

Detector changes are guarded by a frozen regression suite:
`python3 scripts/defect_lint_regression.py` re-lints the pre-fix git
blobs of ~45 confirmed defects (data/derived/defect_lint_regression.jsonl)
and asserts every proven catch still fires.

Reviewing a patch or an old version: lint the candidate file directly
with `--generator-file /path/to/generator.py <task_id>`.

## Semantic hooks (`scripts/generator_semantic_gate.py`) — the task-linked gate

Everything above measures **morphology marginals** (height, width, palette
size, object counts, envelopes). None of it can express *"this lesson
identifies the rule"* — which is why `7d09ccad28c8` sat at rule_smoke 120/120
with a wrong key→direction mapping, and `1ce259f214c8` passed the distribution
gate with 0/600 strict lessons. The semantic gate closes that hole by running
hooks **you** declare in the generator module.

**The normative spec is [`SEMANTIC_GATE_CONTRACT.md`](SEMANTIC_GATE_CONTRACT.md)
(v1, frozen 2026-07-24; amended v1.1 2026-07-25).** Read it before authoring a
hook — return conventions, gate steps and exit codes live there and are not
repeated here. This section is the author-facing summary only.

Declaring **no** hooks is lawful: the gate prints a LOUD advisory, records
`status="NO_CONTRACT"`, and the battery stage stays green (advisory, never
blocking). Declaring a hook that fails is a hard battery failure.

All three hooks are pure: do not mutate the input, do not touch global RNG.

| hook | signature | the gate does |
|---|---|---|
| `strict_canonical_like` | `(grid) -> list[str] \| bool` | Runs the pinned per-band census AND feeds the task's REAL canonical train/test inputs to it. FAILs if the pooled census rate is 0, or if the hook rejects any canonical input (an over-tight predicate disowning its own manifold). |
| `SEMANTIC_WITNESSES` | `dict[str, Callable[[grid], bool]]` | Counts firings per witness per band over the same census. A declared witness with 0 pooled firings FAILs — "documented but never generated" is the defect this gate exists for. Firing in some bands but not others WARNs. |
| `lesson_identifiable` | `(demos, query) -> list[str]` | Materializes lessons (`EXAMPLES_NEEDED` demos + 1 query) with real outputs from the canonical Racket rule, PER BAND (`difficulty` is passed through to every demo/query draw) at a coprime `sample_index` stride, and FAILs on any lesson you report as unidentifiable — quoting its `(band, seed, sample_index)` replay tuple. |

Five OPTIONAL declarations were added in contract v1.1 (2026-07-25). None of
them exists anywhere in the corpus yet, so nothing below can change an existing
verdict; each closes a measured way for the gate to be green and prove nothing.

| declaration | shape | what the gate does |
|---|---|---|
| `SEMANTIC_RIVALS` | `dict[str, Callable[[grid], grid]]` | named WRONG rules, available to the two checks below |
| `WITNESS_RIVALS` | `dict[str, list[str]]` | a witness CLAIMS that where it fires, ≥1 named rival differs from the canonical answer. The gate applies the canonical Racket rule and VERIFIES it: no firing with a disagreeing rival = FAIL ("witness PROVES NOTHING"); some = WARN. A witness with no claim is reported WEAK (`--require-rival-witness` makes it a warning) |
| `LESSON_COMPETITORS` | `dict[str, Callable[[grid], grid]]` | named rival solvers scored against every lesson, so an unidentifiable lesson NAMES which competitor survived the demos instead of only counting |
| `CANONICAL_SHORTCUTS` | `dict[str, Callable[[grid], grid]]` | shortcuts checked against the REAL canonical pairs. One that reproduces EVERY canonical output cannot be falsified by canonical at all — the gate says so and looks for a generated counterexample witness of the same name |
| `schedule_profile` + `SCHEDULE_PROFILES` | `(seed, sample_index, difficulty=None) -> Hashable`, sequence | reports observed profile coverage per band; a declared profile the census never visits WARNs (modular aliasing reads as a missing branch otherwise) |

`strict_canonical_like` accepts **two** return conventions, dispatched on
TYPE — never on truthiness (`True` is never read as "one finding", and `[]`
vs `False` never collapse):

| return | meaning |
|---|---|
| `[]` | lawful |
| `["reason", …]` | not lawful, with reasons |
| `True` | lawful |
| `False` | not lawful (recorded as `predicate returned False`) |

Prefer the `list[str]` form in new hooks — the reasons are what make a gate
failure diagnosable, and they surface in the JSON as ranked `top_reasons`.
The bool form is permanently supported, not deprecated. `lesson_identifiable`
is `list[str]`-only; returning a bool from it is a contract violation.

Anything else (int, `None`, str, …) is a contract violation and FAILs loudly.

### Worked example

```python
# puzzle_generators/per_puzzle/<task_id>/generator.py

def strict_canonical_like(grid):
    """[] when `grid` is a lawful instance of THIS task's canonical manifold.

    Stricter than `self_check`: self_check asks "well-formed instance of my
    teaching grammar", this asks "would a reviewer call this canonical-like
    for this specific task". It replaces the (h, w, palette_size) tuple.
    """
    reasons = []
    h, w = len(grid), len(grid[0])
    if h != w:
        reasons.append(f"canonical is square, got {h}x{w}")
    colors = {v for row in grid for v in row}
    if 5 not in colors:
        reasons.append("no color-5 separator (canonical uses 5, not 9)")
    if len([c for c in colors if c != 0]) < 2:
        reasons.append("fewer than 2 non-bg colors: nothing to disambiguate")
    return reasons


SEMANTIC_WITNESSES = {
    # Every named branch the task must ACTUALLY demonstrate, in every band.
    "marker_top":    lambda g: any(v == 4 for v in g[0]),
    "marker_bottom": lambda g: any(v == 4 for v in g[-1]),
    "blocked_ray":   lambda g: any(v == 8 for row in g for v in row),
}


def lesson_identifiable(demos, query):
    """[] when the demos uniquely determine the answer to `query`.

    `demos` is a list of {"input", "output"} dicts; `query` is one such dict.
    Return reasons when a plausible COMPETING rule consistent with every demo
    would give a DIFFERENT query answer.
    """
    query_colors = {v for row in query["input"] for v in row}
    demoed = {v for d in demos for row in d["input"] for v in row}
    missing = sorted(query_colors - demoed)
    if missing:
        return [f"query uses colors {missing} no demo ever shows"]
    return []
```

Run it directly while authoring:

```bash
python3 scripts/generator_semantic_gate.py <task_id> --per-band 150 --lessons 12 --strict
```

…or as its own battery stage (`semantic_gate`, ordered right after
`profile_floor` — it is the semantic companion to the profile floor):

```bash
bash scripts/run_generator_battery.sh <task_id> after semantic_gate
```

The battery pins `--per-band 150` deliberately. Census seeds derive from
`(task_id, band, index)`, so a larger census is a strict SUPERSET of a smaller
one — raising it can only ADD witness firings. The rarest lawful witness cell
in the hooked corpus fires at p≈0.033, which spuriously trips the band-partial
WARN at `--per-band` 12/20/30; at 150 it has 7 hits of margin. Use the same
number when reporting evidence so every worker quotes the same census.

## Reproducibility contract

```python
generate(seed=42, sample_index=3) == generate(seed=42, sample_index=3)  # always True
```

Bitwise identical. Any failure of this contract is a bug — most
commonly caused by:
- Using bare `random.Random()` instead of `ctx.draw_rng(label)`.
- Iterating over a `set()` (Python preserves insertion order for
  dicts, not sets — sort before iterating if order matters).
- Calling external libraries that have their own RNG state.

## Worked example: `952a094c`

Concept: "Inside-corner cells of a single rectangle move diagonally
to opposite outside corners; clear the inside corners."

```python
# puzzle_generators/per_puzzle/952a094c/generator.py
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "952a094c"
VERSION = "1.0.0"
TASK_ID = "952a094c"
CONCEPT_HASH = "fcd5c4e2d3e9"  # from data/derived/concepts.jsonl
SUMMARY = (
    "A single solid rectangle of one color in a uniform-color grid; "
    "the four inside-corner cells of the rectangle have four distinct "
    "non-rect colors."
)
INVARIANTS = [
    "exactly one solid rectangle of color rect_color",
    "the rectangle's 4 inside-corner cells have 4 distinct non-rect colors",
    "background is uniform color bg, distinct from rect_color and corner colors",
    "rectangle has at least 1 cell of margin from every grid edge",
    "rectangle dimensions: at least 5x5 (so inside corners exist)",
]
AXES = {
    "bg":            {"type": "color",     "default": "rng",            "valid": "0..9"},
    "rect_color":    {"type": "color",     "default": "rng",            "valid": "0..9 != bg"},
    "corner_colors": {"type": "colors[4]", "default": "rng_distinct",   "valid": "0..9 distinct, != bg, != rect_color"},
    "grid_h":        {"type": "int",       "default": "rng 10..14",     "valid": "10..18"},
    "grid_w":        {"type": "int",       "default": "rng 10..14",     "valid": "10..18"},
    "rect_h":        {"type": "int",       "default": "rng 5..h-3",     "valid": ">=5, <= h-2"},
    "rect_w":        {"type": "int",       "default": "rng 5..w-3",     "valid": ">=5, <= w-2"},
    "rect_rr":       {"type": "int",       "default": "rng with margin","valid": "1..h-rect_h-1"},
    "rect_rc":       {"type": "int",       "default": "rng with margin","valid": "1..w-rect_w-1"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    bg          = ctx.draw_color("bg")
    rect_color  = ctx.draw_color("rect_color", exclude={bg})
    corners     = ctx.draw_distinct_colors("corner_colors", n=4,
                                            exclude={bg, rect_color})
    h           = ctx.draw_int("grid_h", 10, 14)
    w           = ctx.draw_int("grid_w", 10, 14)
    rh          = ctx.draw_int("rect_h", 5, h - 3)
    rw          = ctx.draw_int("rect_w", 5, w - 3)
    rr          = ctx.draw_int("rect_rr", 1, h - rh - 1)
    rc          = ctx.draw_int("rect_rc", 1, w - rw - 1)

    g = full_grid(h, w, bg)
    draw_rect(g, rr, rc, rh, rw, rect_color)
    g[rr + 1     ][rc + 1     ] = corners[0]   # top-left inside
    g[rr + 1     ][rc + rw - 2] = corners[1]   # top-right inside
    g[rr + rh - 2][rc + 1     ] = corners[2]   # bottom-left inside
    g[rr + rh - 2][rc + rw - 2] = corners[3]   # bottom-right inside
    return g
```

To produce 50 instances:

```python
from puzzle_generators.runner import run_batch
batch = run_batch("952a094c", n=50, n_train=4, n_test=1)
# batch is a list of {"train": [...], "test": [...]} dicts
```

To produce instances with a fixed background:

```python
batch = run_batch("952a094c", n=50, bg=5)  # all use gray bg
```

## Helper library (`puzzle_generators/helpers/`)

The helpers are minimal — only what 2+ generators want. **Don't add a
helper preemptively.** Lazy growth keeps the API surface small.

### `grid.py`

| Function                              | Purpose                                  |
|---------------------------------------|------------------------------------------|
| `full_grid(h, w, color) -> grid`      | New `h*w` grid filled with `color`.      |
| `clone_grid(g) -> grid`               | Deep copy.                               |
| `draw_rect(g, r, c, rh, rw, color)`   | Mutate: solid rectangle (top-left + h/w). |
| `draw_rect_outline(g, r, c, rh, rw, color)` | Mutate: perimeter cells (top-left + h/w). |
| `fill_box(g, r1, c1, r2, c2, color)`  | Mutate: solid rectangle by **inclusive corners**. Mirrors Racket `(draw-rect-filled g r1 c1 r2 c2 color)`. |
| `draw_frame(g, r1, c1, r2, c2, color)`| Mutate: perimeter by **inclusive corners**. Mirrors Racket `(draw-rect-outline g r1 c1 r2 c2 color)`. |
| `paint_at(g, r0, c0, cells, color)`   | Mutate: stamp `cells` (relative offsets) at `(r0, c0)` with `color`. OOB cells silently skipped. |
| `paint_cells(g, cells, color)`        | Mutate: paint absolute `(r, c)` cells with `color`. |
| `paste(g, sub, r, c)`                 | Mutate: paste `sub` at `(r, c)` in `g`.  |
| `set_cell(g, r, c, v)`                | Mutate: assign one cell.                 |

**Convention.** Two coordinate idioms coexist by design:

- `(r, c, rh, rw)` — top-left + height/width. Used by `draw_rect`,
  `draw_rect_outline`, generator-side rectangle placement.
- `(r1, c1, r2, c2)` — inclusive corner pair. Used by `fill_box`,
  `draw_frame`, and **mirrors the Racket vocabulary** (`obj-bbox`,
  `draw-rect-*`, `subgrid`, `crop`). Prefer this when the calling code is
  parallel to a Racket rule that uses the same corners.

### `palette.py`

| Function                                       | Purpose                          |
|------------------------------------------------|----------------------------------|
| `random_palette(rng, n, exclude)`              | n distinct colors not in `exclude`. |
| `non_bg_colors(bg)`                            | All colors `0..9` except `bg`.   |

### `shape.py`

| Function                              | Purpose                              |
|---------------------------------------|--------------------------------------|
| `rect_cells(rh, rw)`                  | List of `(r, c)` for a solid rectangle (origin 0,0). |
| `rect_outline_cells(rh, rw)`          | Perimeter cells of an `rh × rw` rectangle. |
| `cross_cells(size)`                   | Plus-sign cells.                     |
| `normalize(cells)`                    | Translate so min `(r, c) == (0, 0)`. |

### `place.py`

| Function                                              | Purpose                          |
|-------------------------------------------------------|----------------------------------|
| `random_position(rng, h, w, margin)`                  | `(r, c)` with given margin from edges. |
| `random_free_cell(g, rng, *, bg, max_tries)`          | Random `(r, c)` where `g[r][c] == bg`, or `None`. |
| `place_no_overlap(rng, g, cells, color, *, padding, max_tries)`| Try to place a shape; `padding=1` enforces a 1-cell gap from existing non-bg content (so the new shape stays a separate component under 4-/8-conn). |

The helpers are **pure Python**, never call out to Racket. The Racket
side only sees the final grid via the runner.

## Anti-patterns

### Don't compute the output

```python
# BAD — the rule is the source of truth, not the generator.
def generate(seed, sample_index, **kwargs):
    g = build_input(...)
    out = my_python_reimplementation_of_the_rule(g)  # ← NO
    return {"input": g, "output": out}

# GOOD
def generate(seed, sample_index, **kwargs):
    return build_input(...)  # runner pipes through the Racket rule
```

### Don't bare-`random`

```python
# BAD
import random
n = random.randint(1, 10)  # ← non-reproducible

# GOOD
n = ctx.draw_int("n", 1, 10)
```

### Don't iterate over sets without sorting

```python
# BAD — set iteration order is implementation-defined
for color in {bg, rect_color, *corner_colors}:
    ...

# GOOD
for color in sorted({bg, rect_color, *corner_colors}):
    ...
```

### Don't read the description at runtime

The description is for the LLM author at code-write time. By the time
the generator runs, all that information is encoded as `INVARIANTS`,
`AXES`, and the function body. Never `import` the description.

### Keep canonical execution fixed; propose parametric variants separately

Parametric authoring prioritizes generators traced to the supplied original ARC
families. Preserve the original reasoning structure while varying one or two
nearby rule choices; retain the canonical default and demonstrations that identify
each setting. This priority is provenance-based, not proof that repaired code
still matches its ancestor. An already approved original may be assigned because
its parameterized extension is missing. Evaluation provenance stays explicit.

The selected per-puzzle execution path uses a fixed canonical rule. Reviewer
direction now also asks for one or two small, meaningful rule parameters where
suitable, with matching Racket and examples. Develop that extension separately
under the task's `workspace/parametric/`; choose parameters once per episode and
retain evidence that its demonstrations distinguish the chosen behavior. Explain
when the family is not suitable. See the packet's `PARAMETRIC-RULES.md` for the
prototype and evidence request. This does not add a production parametric API or
extend approval of the canonical rule to new variants.

```python
# BAD — replacing the selected canonical rule inside input generation.
def generate(seed, sample_index, **kwargs):
    rule_template = ...  # ← never modify the rule from the generator

# GOOD
def generate(seed, sample_index, **kwargs):
    return build_input_grid(...)
```

Existing generic generators can emit a program with each complete task; that
separate interface does not change the selected per-puzzle contract above.

## Authoring checklist

- [ ] `GENERATOR_ID`, `VERSION`, `TASK_ID`, `CONCEPT_HASH`, `SUMMARY` set.
- [ ] `INVARIANTS` lists every constraint the generator guarantees.
- [ ] `AXES` documents every kwarg, with type, default, and valid range.
- [ ] All randomness goes through `ctx.draw_*` — no bare `random.*`.
- [ ] `generate(seed=42, sample_index=3)` is bitwise reproducible.
- [ ] Returns a grid, not a `{train, test}` dict — the runner builds those.
- [ ] 50 instances at default axes: all distinct by `content_hash`.
- [ ] 50 instances: rule round-trips without error on each.
- [ ] Axis-override smoke test: passing `bg=5` produces grids using `bg=5`.
- [ ] Semantic hooks declared (or a deliberate, stated decision not to) —
      `strict_canonical_like` / `SEMANTIC_WITNESSES` / `lesson_identifiable`,
      green under `run_generator_battery.sh <task_id> after semantic_gate`.

## Related docs

- [`SEMANTIC_GATE_CONTRACT.md`](SEMANTIC_GATE_CONTRACT.md) — normative spec for
  the three semantic hooks (summarized above).
- [`PUZZLE_GENERATOR_ROADMAP.md`](PUZZLE_GENERATOR_ROADMAP.md) — phased plan.
- [`RACKET_DSL.md`](RACKET_DSL.md) — the Racket side (rules).
- [`RACKET_COMMENT_STYLE.md`](RACKET_COMMENT_STYLE.md) — how Racket rules document themselves.
