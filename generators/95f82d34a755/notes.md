# Working notes: 95f82d34a755

## Current rule and source

Version 3.3.0, generator SHA-256
`961a4db78c62c2cecdec6fa7f3a20156d58a479c80f497d290b8d45c281d393a`.
The top border contains column labels and the left border contains row labels.
The output removes both borders and writes the row label exactly where it equals
the corresponding column label; all other cells are 0. The canonical Racket
rule and declared `RULE_HASH=2d47dff0a44c` were not changed.

## Repaired teaching defect

The five canonical labeled pairs admit two strong executable shortcuts:

- `canonical_extent_only`: apply equality only inside the largest canonical
  4x5 output envelope.
- `first_two_occurrences_only`: ignore third-and-later occurrences of a label
  on either header axis.

The prior 3.1.0 schedule did not name or reliably refute them. An intermediate
single 8x9 `multi_shared` anchor fixed ordered lessons but left 9/72 semantic
smoke rotations ambiguous when that anchor became the query. Version 3.3.0
uses independent 8x9 `multi_shared` and `cross_repeat` anchors. The latter uses
its shared pivot as filler, guaranteeing both third occurrences and matches
outside the canonical envelope. Any six consecutive items therefore retain at
least one dual witness after any query is held out. Explicit dimension overrides
still take precedence over schedule anchors.

Executable declarations are in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, `WITNESS_RIVALS`, and `BRANCH_WITNESSES`. The exact retained
counterexample is `counterexamples/canonical-shortcut-witness.json`; the reusable
Racket-backed probe is `workspace/probe_canonical_shortcuts.py`.

## API repair and evidence

The baseline accepted `sample_index=True`, `False`, `1.0`, `"1"`, and `-1`.
`_validate_sample_index` now requires a literal nonnegative integer. The final
battery is 12/12 green; focused tests are 20/20 green. A required-rotation census
materialized 300 lessons (100 per band), scored 1,800 pairs and 1,800 query
rotations, and found 0 ambiguities or scoring errors across 1,794 unique inputs.
The source-bound probe additionally checked all five canonical pairs, 60 Racket-
labelled scheduled cases, 40 consecutive windows, and 240 leave-one-out rotations.

## Limits and open scope

These measurements cover the six declared rival identities and generic searched
mutations reported by the census; they are not a proof of unique induction
against every imaginable rule. The deterministic five-role schedule is tested
for starts 0-9 at seed 20261012 and the production random census described above.
No approval or training-admission state was changed.

Prior evidence used as a lead: the selected baseline review index and retained
`review-54abfd176cd72e82-v0001` audit, which reported no issue but did not test the
two canonical-fitting shortcuts above.
## Current reviewer considerations

Source SHA-256: `961a4db78c62c2cecdec6fa7f3a20156d58a479c80f497d290b8d45c281d393a`.

# Decisions: 95f82d34a755

## D1 — Treat canonical-fitting generalizations as executable contracts

**Choice.** Added `canonical_extent_only` and `first_two_occurrences_only` to
`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`, with
`WITNESS_RIVALS` linking each to a measurable input property.

**Why.** Both rules fit all five usable canonical pairs exactly, so merely adding
more random equality tables would not establish that generated lessons teach the
intended unbounded rule. Executable declarations let the semantic gate, census,
and future reviewers measure the actual distinction.

**Rejected alternatives.** A prose-only warning was rejected because it can drift
from code. A single hand-written counterexample was rejected because it would not
show production lesson coverage. Generic rivals alone were insufficient because
these two shortcuts are task- and canonical-specific.

## D2 — Preserve the five-role schedule, add two independent dual witnesses

**Choice.** Kept the five semantic profiles and official 4x5/5x6 anchors. Scheduled
both `multi_shared` and `cross_repeat` at 8x9. For `cross_repeat`, both headers keep
two shared labels and an axis-specific label, then fill remaining positions with
the shared pivot.

**Why.** The first intermediate repair had one 8x9 `multi_shared` witness. Ordered
lessons passed, but the required semantic smoke found 9/72 ambiguous rotations when
that one item became the query. Two independent witnesses guarantee that any one
held-out item leaves another in the five demonstrations. Pigeonhole bounds make
the guarantee structural: the repeated pivot must have a third occurrence and a
match beyond the canonical 4x5 output envelope.

**Rejected alternatives.** Increasing `EXAMPLES_NEEDED` would change lesson size
and downstream cost. Randomly hoping for a second witness failed to provide a
contract. Making all five examples large would erase canonical-scale support and
unnecessarily narrow the distribution. Declaring a schedule period was rejected
because this generator does not provide an exhaustive period-census contract; the
small cycle is instead directly tested and production-censused.

## D3 — Keep explicit overrides authoritative

**Choice.** Schedule dimensions are injected only when neither `grid_h` nor
`grid_w` is explicitly supplied. `scene_profile` is injected only when absent.

**Why.** Exact controls are part of the public generator contract. The new teaching
anchors must not silently defeat author requests or override-gate expectations.
A regression requests a 4x5 `multi_shared` item at the extended-anchor residue and
confirms all four advertised axes are observed exactly.

## D4 — Separate branch coverage from rival evidence

**Choice.** The six pre-existing positive witnesses are named in
`BRANCH_WITNESSES`; only `third_shared_occurrence` and
`match_outside_canonical_extent` make explicit rival-disagreement claims.

**Why.** A positive feature can be pedagogically useful without causing a specific
rival to disagree on every firing grid. The first semantic run correctly warned
that the old declarations blurred this distinction. The split makes the gate’s
claims truthful and reusable.

## D5 — Enforce strict `sample_index`

**Choice.** Reject any value whose exact type is not `int`, and reject negative
integers before schedule arithmetic or `GenCtx` construction.

**Why.** The baseline strict detector reproduced five accepted invalid values.
Coercing with `int(...)` would preserve the bug by accepting booleans, floats, and
strings. TypeError handles non-integers; ValueError handles negative integers.

## D6 — Add a reusable Racket-backed probe

**Choice.** Built `workspace/probe_canonical_shortcuts.py` plus pure-helper tests.
It loads the selected bytes, iterates actual rival declarations, checks all
canonical pairs, labels the minimal scheduled draw set via public `Catalog.apply`,
audits ordered windows and all leave-one-out rotations, and writes an exact witness.

**Why.** This makes the key claims replayable by future agents without private APIs
or copied rule logic. It also catches source drift through hashes and refuses to
overwrite an existing output directory.

## D7 — Preserve the frozen fixture

**Choice.** Restored `tests/test_generator_95f82d34a755.py` byte-for-byte to the
packet version and placed reviewer regressions in `tests/test_review_shortcuts.py`.

**Why.** The duties mark the baseline fixture as frozen. The new portable tests use
`find_root`, `canonical_pairs`, and `load_selected_generator`, so they work in both
repository and staged-runtime layouts.

## Measured limits

The exhaustive task-local probe covers starts 0–9 at one fixed seed across default,
easy, medium, and hard bands; the production census independently covers 100
lessons per band with deterministic census seeds and every query rotation. Results
are finite checks against six unique declared competitors plus the census’s generic
mutations. They do not establish logical uniqueness against all possible programs.
No Racket rule, authority file, approval state, or training-admission state changed.

## 2026-10-25 native parametric build

Built a task-local native family with one parameter, `match_alignment`. The
`in_place` default returns the catalog-selected Racket program byte-for-byte.
The `first_match_to_origin` branch constructs the complete header-equality
field, derives its first nonzero coordinate in row-major order, and cyclically
shifts the entire field by that input-dependent row/column offset. Sampling is
independent of the hidden setting, supports 3–6 demonstrations and 1–4
prefix-stable queries, and retains a 30×30 stress input whose 29×29 field has a
nontrivial delayed first match and three match colors.

Reviewer verification is source-bound and retained under
`workspace/parametric/evidence/` and `checks/95f82d34a755/`: 10 focused tests,
20 existing task tests, a 20-seed × 2-setting self-audit with no finite-rival
ambiguity, protected-Racket native qualification for four jobs, and a replayed
wrong-intermediate causal witness. This is reviewer-ready prototype work only;
owner qualification/acceptance and any training admission remain unperformed.
