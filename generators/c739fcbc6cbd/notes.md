# Current notes: c739fcbc6cbd

Version `3.1.0`; final reviewed generator SHA-256
`cbcf3f9249c0f98cdc8bb021e7e16156d5a1e277d7b65abca53ac57ab308bd24`.
The canonical Racket authority and `RULE_HASH=689b63050826` are unchanged.

## Intended rule

Treat color `0` as background. Select the first two nonzero cells in increasing
color order and then row-major order within a color. Let their row and column
separations be `dr` and `dc`. Use full horizontal bands when `dc == 0` or
`0 < dr < dc`; otherwise use full vertical bands, so equality selects columns.
The two marker colors are phases separated by the active-axis distance and
repeated with period twice that distance. Cells before the earlier active-axis
coordinate remain zero. Additional higher-color cells are ignored by the rule.

## Review repairs

- `generate()` now rejects bool/float/string seeds and sample indexes and rejects
  negative sample indexes before schedule arithmetic.
- The strongest canonical-fitting rival is executable as
  `row_major_first_two`: it selects the first two nonzero cells spatially rather
  than by color. It fits all five canonical pairs because each has only two dots.
- `high_color_decoys` now guarantees a lawful counterexample by placing a
  higher-color decoy earlier in row-major order than the second intended marker.
  The exact retained witness is
  `workspace/counterexamples/row_major_first_two.json`; its intended output is
  also checked by `checks/counterexample/racket.json` in the review return.
- Default lessons use a declared two-slot schedule: an even slot is a guaranteed
  row-major counterexample and an odd slot samples the broad non-witness profile
  pool. Explicit `scene_profile` overrides bypass this schedule exactly.
- Executable witness, rival, canonical-shortcut, lesson-competitor and
  `lesson_identifiable` hooks now describe the finite teaching claim.

## Measured evidence

The strict after battery passed all 12 stages. The task-local review suite passed
27 tests. The fixed-seed exhaustive schedule check materialized all two starts in
each band (6 lessons, 24 query rotations) with no declared-rival ambiguity. A
larger production census materialized 300 lessons (100 per band), 1,200 pairs,
1,200 query rotations and 1,008 unique inputs, again with no declared-rival
ambiguity, warnings or scoring errors. Profile-floor support was 7 exact and 18
envelope hits in 60 draws, with at least one exact hit in each band.

The portable aggregate `task_tests` stage remains preflight-blocked by the
inherited frozen fixture's fixed `__file__.parents[...]` canonical-data path.
The fixture was deliberately not edited; direct new tests pass, while aggregate
portable status must remain blocked until the maintainer migrates that fixture.

## Separate proposed parameter extension

`workspace/parametric/` contains a non-production prototype that chooses
`period_factor` once per episode from `{2, 3}`; canonical default is `2`. Both
instantiated Racket programs, three demonstrations plus one query per setting,
public challenges, and hash-bound probe evidence are retained. All 8 Racket
labels matched an independent Python mirror and all 8 differed under the other
factor. This is a proposed family extension, not a change to selected execution
or an approval claim.

## Limits and open questions

The semantic result is finite: it refutes the declared row-major rival, not every
possible induction. The two-slot schedule deliberately correlates witness type
with sample-index parity, and the broad slot excludes `high_color_decoys`; this
is a curriculum choice rather than independent profile sampling. The generator
supports 2..5 dots and bounded geometries, not every input accepted by the Racket
program. The separate factor-3 prototype still needs an independent family-level
decision before any production integration.
## Current reviewer considerations

Source SHA-256: `cbcf3f9249c0f98cdc8bb021e7e16156d5a1e277d7b65abca53ac57ab308bd24`.

# Decisions: c739fcbc6cbd

## D1 — preserve the canonical rule

The canonical transformation already matches all public pairs, rule smoke and
authority sync. The measured baseline defects were in the Python call contract
and lesson support, not in Racket semantics. I therefore left the canonical row,
base solution and `RULE_HASH=689b63050826` untouched. Changing Racket merely to
encode sampler behavior was rejected because it would alter the task rather than
repair the generator.

## D2 — validate public scalars before context or schedule use

`seed` and `sample_index` now require `type(value) is int`, rather than
`isinstance(value, int)`, so booleans do not pass as integers. Negative
`sample_index` fails before modulo arithmetic. Alternatives rejected: coercion
would merge distinct calls and hide errors; relying on `gen_ctx` left the exact
baseline defect in place. Cost: callers that previously passed coercible values
receive a deliberate exception.

## D3 — choose `row_major_first_two` as the primary rival

The original rationale for omitting semantic declarations was undocumented.
The strongest simple canonical-fitting rival I found is spatial selection: scan
row-major and use the first two nonzero cells. It fits all five canonical pairs
because none contains a decoy. It is close to the intended mechanism, total on
the lawful task domain, and differs as soon as a later-color decoy precedes the
second selected color. This makes it more useful than a superficial constant or
shape-only rival.

The retained 17×21 counterexample has nonzero cells
`(0,0)=1`, `(0,19)=8`, `(2,1)=5`, `(9,9)=7`, `(13,10)=9`; all unspecified cells
are zero. Intended color-major selection uses colors 1 and 5, while the rival
uses 1 and 8. Canonical Racket, the independent mirror and the rival outputs are
all retained and hash-bound.

## D4 — guarantee the witness inside `high_color_decoys`

The prior decoy profile allowed extra colors but did not guarantee that spatial
and color order disagreed. The repaired profile fixes the first intended marker
at `(0,0)`, places the second intended lower in the grid, and places at least one
higher-color decoy later in row 0. Additional higher-color decoys remain random.
This preserves the intended selection rule while making the witness predicate
true by construction.

Rejected alternatives: post-generation rejection would obscure provenance and
could loop; a low-probability decoy would not support a short-lesson guarantee;
a hand-authored one-off witness would not test the production sampler.

## D5 — use a two-slot default teaching schedule

`EXAMPLES_NEEDED=3` and `LESSON_SCHEDULE_PERIOD=2` make every contiguous
three-demo window contain at least one guaranteed counterexample, and every
single query rotation still leaves at least one in the demos. Even indexes use
the witness profile; odd indexes use the broad pool. Explicit profile overrides
bypass this curriculum because an exact authoring request must remain exact.

Cost and limit: schedule slot and scene family are correlated, and independently
resampled, shortened or manually reordered lessons do not inherit the guarantee.
A longer period or probabilistic witness frequency was rejected because neither
improves the finite contract enough to justify weaker exhaustiveness.

## D6 — restore novelty with broad-pool weighting, not canonical replay

The first implementation over-weighted exact public profiles and produced only
1,942 unique inputs in the frozen 2,600-draw probe, below the required 2,050.
The final odd-slot pool duplicates both public and non-witness general profiles
once, preserving all non-witness families without making public replay dominant.
The rerun produced 2,187 unique inputs and 2,104 unique outputs and passed the
strict profile floor. This weighting is a bounded engineering choice, not a
claim of independent uniform axes.

## D7 — declare a finite semantic contract honestly

The same callable object is bound in `SEMANTIC_RIVALS`,
`CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; the witness checks actual output
disagreement. `lesson_identifiable` reports only whether this named rival fits
all demos while changing the query. I did not claim universal identifiability.
The random and exhaustive censuses additionally report generic rival results,
but untested hypotheses remain unknown.

## D8 — keep `period_factor` outside production

For the original ARC-family priority, the smallest plausible rule parameter is
the multiplier on active-axis separation. The prototype permits `{2,3}`, keeps
2 as canonical default, and chooses one factor once per episode. Selection,
axis, prefix and colors remain unchanged. Each retained pair distinguishes the
settings, avoiding a parameter that demonstrations cannot identify.

The prototype has exact Racket programs and Racket-derived labels, but it remains
under `workspace/parametric/`; production imports and selected execution never
use it. Integrating factor 3 without a separate family-level decision was
rejected because the assignment grants authoring priority, not variant approval.

## D9 — do not edit the frozen fixture

The portable task-test stage identifies a fixed-parent canonical path in the
inherited frozen test. Duties reserve that fixture for maintainer migration. I
kept the failure, ran the new task-local tests directly, and report aggregate
portable status as blocked rather than converting it into a false pass.

## D10 — evidence retention and compression

The 300-lesson full report was 23,031,224 bytes and would consume nearly the
entire return budget. It is retained losslessly as deterministic gzip. The
compression manifest records original/compressed sizes and SHA-256 values and a
restoration command; the compact summary remains directly readable. Earlier
failed or blocked evidence was retained, while no duplicate repository or
runtime tree was added.
