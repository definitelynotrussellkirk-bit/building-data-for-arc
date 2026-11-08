# Working notes: 42a28f889145

## Intended rule and owned domain

The input is a rectangular `0`-background grid with exactly two uniformly
colored, four-connected nonzero objects. Their colors are distinct and their
column ranges are separated by at least one all-background column. Sort the
objects left-to-right and exchange their colors while preserving every occupied
cell, shape, position, and background cell.

Generator v3.0.0 owns heights 7–12, widths 9–16, six connected shapes of 3–6
cells, ordered pairs of those shapes, and every unordered pair of ARC colors
1–9. It emits both left/right numeric color orders. The selected Racket
reference was not changed; the pinned canonical `RULE_HASH` is `57cc84264d9e`.

## Baseline findings (v2.2.0)

The immutable before battery on generator SHA-256
`b0d4e878d9f31fd2d07e42ee3e790a54306f9ea3ed0ade4674094fa4aeedd7a4`
reported 7 green, 2 advisory, and 3 failed stages. The failures were contract
failures rather than a wrong reference rule:

- no pinned `RULE_HASH`;
- `shape_pair`, `position_bias`, and `density` were advertised but not usefully
  probeable;
- `palette_size` and `n_distinct_colors` claimed a value of 3 although generation
  always produced exactly two colors, and several palette/texture controls were
  accepted but pixel-dead;
- unknown and malformed overrides were silently accepted;
- helpful and degenerate `texture` values shared one domain even though the
  degenerate values intentionally violated `self_check`;
- exact canonical-profile support was only 2/60, with no medium or hard exact
  hits;
- no executable semantic witness, rival, or lesson-identifiability contract was
  declared.

`evidence/associated_notes.jsonl` was empty, so no prior return was used as a
repair lead. The imported v2.2.0 source and the before battery were the evidence.

## Strongest canonical-fitting shortcut

All three labeled canonical pairs have the smaller numeric color on the left and
the larger color on the right. Therefore the rival rule “paint the left object
with the larger color and the right object with the smaller color” fits every
canonical output without representing a swap.

A lawful generated counterexample uses seed 9, sample index 1, and overrides
`grid_h=7`, `grid_w=9`, `shape_pair=0`, `color_pair=0`. Its left object is color
2 and its right object is color 1. The intended swap changes them to 1 and 2;
the descending-sort rival leaves the input unchanged. The independent Python
oracle and selected Racket authority agree, while the rival differs. Reproduction
files are in
`counterexamples/review-86f9efd9c687c23d-v0001/`; the Racket evidence is bound
to final generator SHA-256
`b2cadd67ac405bbcf3a5ffba4fda02d6c483c1a028d760830fa74c91f38ac5a6`.

## Decisions in v3.0.0

1. **Replace the nine-axis declaration with four exact controls.** `grid_h`,
   `grid_w`, `shape_pair`, and `color_pair` are all directly requestable and
   exactly recoverable from pixels through `observe_overrides`. Singleton,
   alias, ignored, and impossible controls were removed rather than simulated.
2. **Validate the public call strictly.** Boolean/non-integer seeds and indices,
   negative indices, unknown difficulty values, unknown axes, wrong types, and
   out-of-range values now fail loudly. This prevents false provenance.
3. **Make layout constructive.** The generator enumerates every legal split of
   horizontal room into left margin, positive inter-object gap, and right margin,
   then chooses one. Boundary axis combinations are covered by tests instead of
   relying on `randint` repairs.
4. **Increase legitimate variation while keeping canonical support.** The shape
   vocabulary grows from four to six connected shapes and permits identical or
   different ordered shape pairs. All 36 unordered nonzero color pairs are
   available. Default height/width draws keep full support but weight canonical
   sizes 7×9/10 strongly enough to satisfy every difficulty band.
5. **Schedule both numeric color orders.** Even `sample_index` places the lower
   color left; odd `sample_index` places the higher color left. Every four-pair
   episode (three demonstrations plus one query), including each cyclic query
   rotation, therefore leaves both orders among the demonstrations. This
   deterministically refutes the descending-sort shortcut.
6. **Declare executable semantics.** `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`,
   `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `LESSON_COMPETITORS`, and
   `lesson_identifiable` all refer to the same concrete rival and witness.
7. **Add portable tests and a reusable probe.** The test suite uses
   `reviewer_support.canonical_pairs`/`find_root` and an independent component
   oracle. `workspace/probe_shortcut.py` replays every declared canonical
   shortcut against canonicals and materializes the exact witness.

## Verification

- Focused target tests: 34 passed.
- Final after battery: 12/12 green, 0 advisory, 0 failed.
- Lesson census: 300 three-demonstration lessons (100 per difficulty), 1,200
  unique input pairs, and all 1,200 held-out query rotations; zero ambiguity,
  hook warnings, materialization errors, or scoring errors against the declared
  rival.
- Reference authority: unchanged; rule hash and authority-sync checks pass.

Exact retained reports live under `WORK/checks/after-v1/`,
`WORK/checks/task-tests-v1/`, and `WORK/checks/lesson-census-v1*.json`.

## Limits and open findings

The finite shape vocabulary is intentionally narrower than all possible
connected polyominoes, and the semantic checks establish identifiability only
against the declared descending-color rival—not against every imaginable rule.
The parity schedule assumes lessons are assembled from four consecutive sample
indices, which is the production materializer tested by the census. Arbitrary
subsampling could remove one color order and should call `lesson_identifiable`
or preserve the same scheduling invariant. No Racket rule change is proposed.
## Current reviewer considerations

Source SHA-256: `b2cadd67ac405bbcf3a5ffba4fda02d6c483c1a028d760830fa74c91f38ac5a6`.

# Repair decisions for 42a28f889145

## Intended outcome

Make the generator a truthful, controllable, canonical-compatible curriculum
for “exchange the colors of two separated objects,” while directly teaching
against the strongest shortcut induced by the canonical demonstrations. The
Racket authority is correct and remains unchanged.

## Decisions retained

### Replace the misleading control surface

The previous generator advertised nine axes, but several were ignored,
unobservable, mutually collapsed, or capable of requesting impossible states
such as three colors for a two-color task. I replaced them with four exact
controls whose values can be recovered from every generated grid:

- `grid_h`: 7–12
- `grid_w`: 9–16
- `shape_pair`: 36 ordered pairs from six connected shapes
- `color_pair`: all 36 unordered pairs from colors 1–9

Unknown, non-integer, Boolean, and out-of-range values now fail loudly. This
was chosen over keeping compatibility aliases because dead aliases would
preserve false provenance.

### Use constructive placement

The layout enumerates legal allocations of left margin, positive gap, and right
margin, then samples one and samples legal rows. This makes every advertised
boundary combination realizable without clamping or retry-dependent repairs.

### Broaden only rule-relevant variation

The shape vocabulary grows from four to six 3–6-cell connected blobs; it
contains every normalized canonical shape and supports identical or different
ordered shape pairs. All color pairs and all declared dimensions remain
requestable. Default dimensions weight 7×9 and 7×10 examples because the
canonical profile is concentrated there, while retaining full support in every
difficulty band.

I rejected arbitrary-polyomino generation for this repair. It would increase
implementation and validation surface without strengthening the key semantic
claim; six distinct shapes already separate color exchange from shape-specific
rules and include canonical support.

### Alternate numeric color order deterministically

The strongest canonical-fitting rival is “put the larger color on the left.” A
purely random left/right order could accidentally produce a three-demo lesson
that never refutes it. Instead, consecutive sample indices alternate color
order: lower-left on even indices and higher-left on odd indices.

Production lessons use three demonstrations and one query from four consecutive
materialized pairs. Every such bundle contains both color orders, and holding
out any one pair still leaves both orders among the other three. This is a
teaching schedule, not part of the transformation rule. The 300-lesson census
used required query rotation and found zero ambiguous production lessons and
zero ambiguous rotations across all 1,200 held-out positions.

### Declare executable semantics

The same named rival is represented in `CANONICAL_SHORTCUTS`,
`SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; the left-color-greater witness is
linked through `SEMANTIC_WITNESSES` and `WITNESS_RIVALS`.
`lesson_identifiable` checks that a supplied demonstration set refutes the
rival. This was chosen over prose-only claims so the semantic gate and future
reviewers can execute the contract.

### Add portable tests and a reusable probe

The new task-local suite uses `reviewer_support.find_root`,
`canonical_pairs`, and `load_selected_generator`, avoiding repository-depth
assumptions. It tests canonical ownership, the independent swap oracle, exact
and strict controls, shape/color support, both color orders, lesson rotation,
and declared rival behavior.

`workspace/probe_shortcut.py` source-binds the selected generator, verifies all
declared canonical shortcuts against labeled canonicals, constructs the exact
witness, and compares the rivals with an independent component oracle.

## Alternatives rejected

- **Retain ignored texture and density controls:** rejected because they create
  unverifiable provenance and had generated invalid/helpful/degenerate overlap.
- **Randomize color order without a schedule:** rejected because a valid random
  draw can still assemble an ambiguous lesson.
- **Change the Racket rule:** rejected; rule smoke and canonical replay showed
  the authority was already correct.
- **Encode the answer as color rank:** rejected as the precise shortcut the
  repair must defeat.
- **Claim universal identifiability:** rejected; the evidence covers declared
  rivals and sampled materialization, not every possible hypothesis.

## Remaining limitations and self-review

The six-shape vocabulary is finite, but the transformation is shape-independent,
all canonical shapes are represented, identical/different pairs are sampled,
and tests verify occupied-cell preservation rather than memorized templates.
The parity schedule introduces a predictable sampling pattern, but not an
output shortcut: the query transformation cannot be inferred from parity alone,
and the required-rotation census found no ambiguity against the declared rival
in 1,200 query positions.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-f3b5dc193d5a6396:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `b2cadd67ac405bbcf3a5ffba4fda02d6c483c1a028d760830fa74c91f38ac5a6`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported audited source b2cadd67ac405bbcf3a5ffba4fda02d6c483c1a028d760830fa74c91f38ac5a6. Bounded clean:34 tests, semantic gate, warning-free defect lint and300 lessons/1200 rotations pass against declared sorting rival. No universal proof. Retain exact target-local evidence (quoted basenames resolve here): `checks/audit/42a28f889145-combined.log` `checks/audit/42a28f889145-combined/RUNTIME_MANIFEST.json` `checks/audit/42a28f889145-combined/checks/42a28f889145_audit_battery_summary.json` `checks/audit/42a28f889145-combined/checks/42a28f889145_audit_commands.jsonl` `checks/audit/42a28f889145-combined/checks/42a28f889145_audit_semantic_gate.json` `checks/audit/42a28f889145-combined/checks/42a28f889145_audit_semantic_gate.log` `checks/audit/42a28f889145-combined/checks/42a28f889145_audit_semantic_gate.ok` `checks/audit/42a28f889145-combined/checks/42a28f889145_audit_semantic_gate.receipt` `checks/audit/42a28f889145-combined/checks/42a28f889145_audit_summary.json` `checks/audit/42a28f889145-combined/checks/task_tests.xml` `checks/audit/42a28f889145-combined/progress.log` `checks/audit/42a28f889145-combined/result.json` `checks/audit/42a28f889145-defect-lint.log` `checks/audit/42a28f889145-defect-lint/RUNTIME_MANIFEST.json` `checks/audit/42a28f889145-defect-lint/checks/42a28f889145_audit_battery_summary.json` `checks/audit/42a28f889145-defect-lint/checks/42a28f889145_audit_commands.jsonl` `checks/audit/42a28f889145-defect-lint/checks/42a28f889145_audit_defect_lint.log` `checks/audit/42a28f889145-defect-lint/checks/42a28f889145_audit_defect_lint.ok` `checks/audit/42a28f889145-defect-lint/checks/42a28f889145_audit_defect_lint.receipt` `checks/audit/42a28f889145-defect-lint/progress.log` `checks/audit/42a28f889145-defect-lint/result.json` `checks/audit/42a28f889145-lesson-census.json` `checks/audit/42a28f889145-lesson-census.log` `checks/audit/42a28f889145-lesson-census.summary.json` Retained assessment manifest: generators/42a28f889145/evidence/bounded-audit-f3b5dc193d5a6396/manifest.json

### Assessment or prior finding

## 42a28f889145

**No issue found after the assigned checks.** I inspected the current source at
SHA-256 `b2cadd67ac405bbcf3a5ffba4fda02d6c483c1a028d760830fa74c91f38ac5a6`,
its declared strongest rival `sort_colors_descending`, portable tests, semantic
contract, defect lint, and generated lessons.

The combined isolated audit passed 34/34 portable tests and its semantic gate
(`checks/audit/42a28f889145-combined/checks/42a28f889145_audit_summary.json`).
The standalone defect lint found no warnings
(`checks/audit/42a28f889145-defect-lint/`). A source-bound census materialized
100 three-demo/one-query lessons per band: 300 production lessons / 1,200 pairs
and all 1,200 query rotations had zero ambiguity, hook warnings, or scoring
errors (`checks/audit/42a28f889145-lesson-census.summary.json`). The declared
rival fits all three canonical pairs and was refuted in every checked generated
lesson.

Limit: this is a finite declared-rival audit, not a proof against every possible
sorting or object-selection shortcut. I did not edit this audit target.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
