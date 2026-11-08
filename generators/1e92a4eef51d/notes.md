# Current notes: 1e92a4eef51d — Axis-Key Reflect

## Intended rule and authority

Cell `(0,0)` is a key. Remove it, crop the remaining nonzero content, then
reflect the crop left/right for key `1` or top/bottom for key `2`. The selected
canonical Racket source was not changed. `RULE_HASH = "bf7a0a12ef08"` pins that
authority.

## Lead and baseline

The retained review `review-c34ea1dcb737f86c:v0001` was used as the lead. Its
audited source hash, `fddc7753aee97521387b1b3538d4f66c5c86edc42ba2508751d639a244c8320c`,
matched the selected baseline. The fresh before battery reproduced the same
root problems: 7 green, 2 advisory, and 3 failed stages. The source lacked a
rule pin, advertised several ignored or dead controls, accepted unknown
controls, provided no exact-axis observer or semantic contract, and could place
three key-1 examples before a key-2 query.

## Selected design

Version `2.0.0` is constructive rather than retry-based. It exposes seven exact,
observable controls whose full Cartesian product is feasible:

- canvas height and width: `7..14`;
- key: `1..2`;
- body size: `4..7` cells;
- body colors: `1..3` distinct colors, never reusing the active key color;
- body components: `1..2` four-connected components;
- aspect relation: `aligned` or `conflict` between key-selected axis and crop
  aspect.

A small table of asymmetric wide shapes covers every `(size, component-count)`
combination; tall shapes are exact transposes. This makes overrides exact
without sampling failure. Every generated grid reserves row 0 and column 0 for
the key, keeps the selected reflection visible, and permits all four canonical
inputs under the same `self_check` domain.

## Curriculum and semantic contract

`LESSON_SCHEDULE_PERIOD = 4` and `EXAMPLES_NEEDED = 3`. The repeating profiles
are:

1. key 1, aligned crop, landscape canvas;
2. key 2, conflicting crop, landscape canvas;
3. key 1, conflicting crop, portrait canvas;
4. key 2, aligned crop, square canvas.

Every three-profile window contains both keys and at least one counterexample to
choosing the axis from crop or canvas aspect. The executable competitors are
`always_horizontal`, `always_vertical`, `crop_aspect_axis`, and
`canvas_aspect_axis`. The last one is also the strongest shortcut that fits all
four canonical labeled pairs. Witness predicates and `lesson_identifiable`
check those claims directly.

The first profile is a permanent `(7,8)` / two-body-color canonical anchor.
This replaced the initial “every eighth cycle” anchor after the repository's
hash-derived profile-floor census produced zero exact hits in medium and hard.
The focused regression reproduces that pinned census, so the fix is not tied to
sequential sample indexes.

## Final evidence

Final generator SHA-256:
`f1ed850f3f0edf2de4ca7b40493df62a055a4fd45ff580fc67c5ec0f89968e7c`.

- Complete after battery: 12/12 green, with rotations required.
- Task-local tests: 29/29 passed.
- Exact override contract: 33,300/33,300 draws accepted, 0 findings.
- Canonical profile floor: all four canonical inputs accepted; 14/60 exact
  profile hits and support in every band.
- Semantic gate: 600/600 strict, 4/4 witnesses, 4/4 rival claims, 12/12 sampled
  lessons identifiable, 0/48 ambiguous rotations.
- Larger census: 300/300 lessons, 1,200 pairs and 1,200 rotations, zero declared
  rival ambiguities or scoring errors; 1,155 unique inputs.
- Declared-period census: all 4 starts × 3 bands and 48 rotations clean at seed
  0.

## Known limits

The shape family is intentionally bounded to 4–7 cells and one or two
components; it does not claim support for every possible asymmetric object.
The finite rival set does not prove unique induction against every imaginable
rule. Fixed-seed schedule enumeration proves all declared residues only at that
seed, while the 300-lesson census samples rather than exhausts the seed space.

Current audit assessment: `review-c34ea1dcb737f86c:v0001` is scoped resolved for the repaired key-teaching/exact-control/canonical-feature findings. See `evidence/current-audit-assessment.json`; acceptance uses reviewer-reported finite checks, with no owner replay or trajectory training admission.
## Current reviewer considerations

Source SHA-256: `f1ed850f3f0edf2de4ca7b40493df62a055a4fd45ff580fc67c5ec0f89968e7c`.

# Decisions — review-623f70badfd8a8d3

## D1 — Preserve the canonical Racket authority

**Prior choice:** the selected generator had no `RULE_HASH` pin, but rule smoke
and authority synchronization were already green.

**Decision:** leave the Racket program unchanged and pin
`RULE_HASH = "bf7a0a12ef08"`.

**Reason/evidence:** all four canonical labels and the Python mirror agree with
the selected source. Changing the rule would have addressed no reproduced
failure and would have increased authority risk. Final `rule_smoke`,
`racket_lint`, and `authority_sync` are green under `checks/after/`.

**Failure mode considered:** a generator repair that silently targets a nearby
horizontal/vertical convention. The rule pin, Racket parity receipts, and
counterexample tests prevent that drift.

## D2 — Replace, rather than patch, the dead-axis sampler

**Prior choice:** eight advertised controls included aliases, singleton labels,
and degenerate textures, while normal generation actually varied only a narrow
canvas range and a random two-color blob. Most overrides were ignored or
clamped by difficulty.

**Alternatives:**

1. Keep the old sampler and add conditional handling for every legacy axis.
2. Mark ignored fields diagnostic while retaining the retry loop.
3. Replace the contract with a smaller constructive set of meaningful axes.

**Decision:** option 3. The seven final axes are all visible and recoverable via
`observe_overrides`.

**Reason/evidence:** it removes misleading controls instead of institutionalizing
them. The final override matrix covers 370 cases, 3 bands, and 33,300 draws with
zero findings. Unknown names are rejected.

**Limit:** this intentionally breaks compatibility with callers relying on the
old misleading `texture`, `palette_kind`, `palette_size`, `position_bias`, or
`density` controls. Those controls did not have reliable semantics to preserve.

## D3 — Use finite constructive shape templates

**Decision:** define asymmetric wide templates for each body size `4..7` and
component count `1..2`; transpose for tall cases.

**Reason:** every advertised joint combination is feasible even on a `7×7`
canvas, and shape asymmetry makes both horizontal and vertical transforms
observable without retrying. A generic random-growth loop was rejected because
it makes exact component, aspect, and visibility controls probabilistic.

**Probe:** task tests request both extreme override combinations in all four
bands and recover every requested value exactly.

**Limit:** templates cover the selected bounded domain, not arbitrary
polyominoes.

## D4 — Make canonical support explicit, not accidental

**Initial decision:** emit canonical dimensions every eighth schedule cycle.

**Observed failure:** the repository profile-floor uses hash-derived,
off-diagonal sample indexes; medium and hard received zero exact-profile hits.
The regression in `tests/test_generator.py` reproduced the exact pinned census
before the repair.

**Reversal:** profile 0 is now always a `(7,8)` canvas with two body colors,
which is exact profile `(7,8,4)` including background and key. Other profiles
continue to provide broad dimensions, so the 128-sample distribution test still
sees at least twelve dimension pairs per band.

**Evidence:** `checks/tdd-profile-red/` records the failure;
`checks/after/...profile_floor.log` records 14/60 exact hits with every band
covered.

## D5 — Link lessons through a four-profile schedule

**Prior choice:** ordinary random sampling could produce three key-1 horizontal
examples followed by a key-2 query. The retained lead records seed 3 with keys
`[1,1,1,2]`.

**Alternatives:** resample lessons after scoring; increase demonstration count;
or construct a schedule whose local windows are identifiable.

**Decision:** retain three demonstrations and use a period-4 linked schedule:
key1/aligned/landscape, key2/conflict/landscape,
key1/conflict/portrait, key2/aligned/square.

**Reason:** every three-item window demonstrates both branches and refutes fixed
axis, crop-aspect, and canvas-aspect rivals. This remains true for every held-out
query position.

**Evidence:** 0/1,200 ambiguous rotations in the production census and all 48
fixed-seed schedule rotations clean.

**Limit:** only declared plausible rivals are scored; universal semantic
identifiability remains unproved.

## D6 — Declare the canonical shortcut explicitly

**Decision:** `CANONICAL_SHORTCUTS["canvas_aspect_axis"]` chooses horizontal on
landscape canvases and vertical otherwise.

**Reason:** this rule exactly matches every canonical labeled pair, so omitting
it would overstate what canonical data alone establishes. Generated conflict
profiles provide executable counterexamples. Seed 708, sample 1 is retained in
`generators/1e92a4eef51d/counterexamples/canvas-aspect-shortcut.json` and checked
against Racket.

## D7 — Strengthen validation and independent helpers

**Decision:** `self_check` now handles malformed objects without throwing and
validates dimensions, ARC cell types, key isolation, body size/color/component
bounds, non-square crop aspect, and visible keyed reflection. The Python
reference and rivals copy inputs and are tested for non-mutation.

**Reason:** a permissive validator would let semantic gates certify a wider,
unintended domain. Canonical inputs are explicitly included in the regression
suite.

## D8 — Test-first repair and retained failures

The initial task test suite was written before production changes and failed
25 tests as expected. A later profile-floor regression was added, observed
failing in medium, and then fixed. Both red receipts are retained. Final task
tests are 29/29 and the complete battery is 12/12 green.

## D9 — No audit-target edits

The assigned audits `778019638a4d` and `5003370f0e31` were examined and
reproduced, but their source files were left unchanged as required. Findings and
receipts are in `AUDIT.md` and `checks/audit/`.
