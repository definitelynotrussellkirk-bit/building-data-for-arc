## 2026-10-24 — Native short-context output-scale family (review-853a0caa6f10cdc4)

**Current disposition: native ready; owner exact-source acceptance pending.**
Production v3.1.0 remains SHA `9bbefffc3281331b8a02b792ecd9475970e6d8f1b477f359e0bef94858901437`,
canonical rule `2f49d92711a1`. The existing output-scale prototype was strengthened
and connected to the native adapter; scale 2 now returns the byte-exact canonical
program, and scale 3 changes only its two output-size multipliers.

The native family supports 2–6 demos and 1–4 queries, defaulting to 3/4. A fixed
six-demo/four-query bank is generated before slicing, so settings share inputs
and count requests preserve prefixes. Its first two examples jointly teach
optional zero padding, contiguous multiplicity, and separated recurrence of both
first and later colors. The fourth query is 10×10 with nine active bands plus
padding; scale 3 gives a fully populated 30×30 continuation. Original input
support remains 4×4..10×10, with all three production pattern classes retained.

The retained old sampler's seed-0/easy/scale-3 two-demo prefix admits a
first-run-per-color shortcut, changing 225 of 441 cells on a query. Its old
checker explicitly required five demos: this was an unsupported short-context
gap, not evidence of accepted training corruption. `short_prefix_probe.py`
replays the saved exact programs and grids without the old implementation.
The new rich motif initially returned one extra active cell; the retained failed
run and period-7/8/9 diagnostic led to an exact-length repair and boundary test.

Final evidence is under `checks/8e6c44aee812/`: **95 tests passed** (including the
six existing prototype tests), **144/144 Python-screen episodes**, and a protected
six-episode audit with **387 executions, 46 labels and 16 extra rivals**, all
extras refuted by the first two demos. Minimum 4×4 native inputs pass both
settings. Two controller exports and eight isolated actor turns pass exact
visible-byte/ID checks. Native qualification passes both settings on seeds 0/17,
three demos/four queries (40 executions); its sibling execution receipt is kept.

The causal intermediate is the full active diagonal and its period. Keeping zero
padding changes 763 final cells; deduplicating active colors changes 170. Both
counterfactuals keep the downstream ring-selection operation unchanged and pass
independent protected replay (`causal/witness.json`, `causal/replay.json`). This
is derived-sequence dependence, not iterative grid-state simulation. Current
source is bound by `workspace/parametric/evidence/manifest.json`; older retained
five-demo reports remain historical.

For the assigned Qwen data-value question, the implemented audit provides one
candidate gate: fit a bounded plausible rival set to the actual visible demos,
and reject only a survivor that changes a query answer. The cheap retained
regression needs six protected executions. An overly contrived rival can reject
useful lessons; keep a scoped rival registry and permit answer-equivalent
survivors. No Qwen accuracy or learning-gain experiment was run.

**Next owner action:** integrate the checked delta, qualify the exact live source,
and run native acceptance. Current receipts do not approve variants or admit
training data. No source, qualification or acceptance claims are transferred
from historical evidence.

---

# Working notes: 8e6c44aee812

## Current rule and scope

Version 3.1.0 retains Racket authority `2f49d92711a1`. Read the main diagonal,
remove optional trailing zero padding, double both input dimensions, and cycle
the active diagonal using `max(row, col)`. Repeated colors remain part of the
sequence. The teaching domain is a square staircase of side 4..10, active period
4..9, at least two nonzero colors, and zero or one final padding band. This is a
deliberate, observable subset of the reference rule's support.

Seed and sample index must be literal Python integers; signed and arbitrarily
large seeds remain legal, while sample indices must be nonnegative. Explicit
periods must be literal integers in 4..9. `None` retains the default axis draw.
All advertised combinations of period, padding, and pattern class remain exact.

## Decisions and reversals in review-2ce1eb0bfd0d6744

The imported 3.0.0 schedule used three demonstrations. Retained audit
`review-35316dedd6e945e7-v0001` showed that preserving only each color's first
contiguous run fits all four canonical pairs and all three demonstrations of
seed 0/easy/indices 5..7, but differs on query 8 in 83 of 100 cells. The retained
input grids are authoritative fixtures; redrawing those indices after editing
the generator would not replay the finding.

The first repair added that rival and five demonstrations. Independent review
then found a more specific rival: preserve every run of the first diagonal
color, but keep only the first run of each other color. It fits the canonical
pairs and two five-demo lessons from the intermediate source
`4b601e6cb5789d1fbb9b3b4497ec8c3ae91e351d54ff1c1c2c7bb47991814da9`.
The ordinary seed 1/easy/indices 6..11 lesson differs in 128/144 query cells;
the seed 0/easy/indices 0..5 population with index 2 held out differs in
148/196 cells. Exact fixtures and provenance are in
`counterexamples/role_conditioned_first_run.json`; the return also retains the
original reference receipt under `checks/intermediate-shortcut/`.

The final schedule keeps five demonstrations and one query. Every six
consecutive inputs include two complex examples with separated reappearances
of both the first color and another color, plus one separated prefix example.
The other slots retain distinct, contiguous-prefix, and contiguous-complex
families. Seed parity varies their association with padding. The combined
period/padding/pattern schedule has declared period 12. Every query holdout
retains evidence against the three run-preservation rivals, both padding
branches, a canonical 5x5 input, a generalized input, and a period above five.

Requiring every pattern category in every five-demo lesson was replaced by
actual rival refutation. Distinct examples remain in global generated support;
forcing that category into each lesson would consume evidence slots without
distinguishing the demonstrated shortcut. Both repetition families remain
available with both padding choices. A second intermediate candidate admitted
two-run `A A B B`; the generic minimal-impostor detector flagged that lawful
inner-block geometry. The broadening was unnecessary: seed 1/index 6 supplies
contiguous complex repeats with padding, while period-four complex inputs can
use `A B A B`. The final source therefore restores the original requirement of
at least three runs for contiguous complex patterns. `A A B B` is explicitly
tested as reference-lawful but outside this teaching subset; its warning is
retained in `checks/after-v2/`. Contiguous complex support is global, while an
optional period-four complex slot can add a third rich recurrence example.
`A B A B` has the same continuation as `A B`, so its witness links include the
role-conditioned rivals; it is not falsely claimed to refute simple deduplication.

## Evidence and limits

The task tests cover scalar contracts, exact axes, purity, reference labels,
retained counterexamples, all six holdouts for every start residue across four
seeds and three bands, and contiguous/separated support. The reusable
`workspace/probe_recurrence.py` obtains public Racket labels, replays the original
83/100-cell finding, and checks 36 production lessons and 216 rotations at a
chosen seed. Its reports distinguish overlapping windows from distinct grids.

The review additionally runs the public schedule enumeration and 100 production
lessons per band with required query rotations. These are finite checks against
declared rivals, not a proof of unique induction or a measured Qwen score gain.
Arbitrary independently sampled or overridden grids are not promised to form
an identifiable lesson; check the assembled lesson with `lesson_identifiable`.

The imported `evidence/review_index.json` is intentionally unchanged. Its open
first-run finding has source-bound repair evidence in this return, but formal
resolution remains a maintainer action; accepting code must not silently close
unrelated retained audits. No Racket authority or audited target was edited.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-35316dedd6e945e7:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `2d84a82e98f71ec383d8c2ca1c6503d37c00459560ed221899201dccf3c46df6`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Adds exact retained first-run role rivals and redundant recurrence teaching schedule;312reportedtests and finalsource qualification support explicit bounded disposition after acceptance. Exact repair accepted with reviewer-reported evidence; no maintainer rerun or closure of other findings.

### Assessment or prior finding

## 8e6c44aee812

**Finding: reproduced lesson ambiguity against an additional canonical-fitting shortcut.** The audited source’s three-example lesson hook accepts the exact generated lesson below, although a plausible alternative fits every demonstration and changes the query answer. The observed reference outputs are correct; the gap concerns the finite lesson contract and demonstrated rule identification.

The rival reads the active diagonal, preserves the **first complete contiguous run of each color**, discards any later separate run of that color, and cycles the resulting sequence through the usual `max(row,column)` staircase. This is distinct from the declared deduplication rival: it preserves repeated cells inside a color’s first run. It fits all **four usable canonical pairs** because every canonical color occupies only one contiguous diagonal run. The public Racket application independently reproduced all four stored canonical labels. [Evidence](checks/audit/8e6c44aee812/evidence.json)

### Exact generated lesson

All four inputs below were produced by `generate(0, sample_index, difficulty="easy")`, with **no overrides**. Every input returns `self_check == []` and matches its declared axes. They are actual default-generator draws, not hand-built inputs outside its grammar.

| Role | Sample index | Full input diagonal | Observed axes | Rival versus Racket |
|---|---:|---|---|---|
| Demonstration 1 | 5 | `[9,9,7,8,8]` | period 5, no padding, complex repeat | Equal |
| Demonstration 2 | 6 | `[8,6,9,1,5,4,0]` | period 6, one padding band, distinct | Equal |
| Demonstration 3 | 7 | `[7,7,7,5,1,6]` | period 6, no padding, prefix run | Equal |
| Query | 8 | `[6,8,6,7,0]` | period 4, one padding band, complex repeat | Different |

The query’s complete 5 × 5 input is:

```text
68670
88670
66670
77770
00000
```

Its correct active sequence is `[6,8,6,7]`; the rival incorrectly shortens it to `[6,8,7]`. Exact 10 × 10 outputs are:

| Row | Selected-rule Racket output | Rival output |
|---:|---|---|
| 0 | `6867686768` | `6876876876` |
| 1 | `8867686768` | `8876876876` |
| 2 | `6667686768` | `7776876876` |
| 3 | `7777686768` | `6666876876` |
| 4 | `6666686768` | `8888876876` |
| 5 | `8888886768` | `7777776876` |
| 6 | `6666666768` | `6666666876` |
| 7 | `7777777768` | `8888888876` |
| 8 | `6666666668` | `7777777776` |
| 9 | `8888888888` | `6666666666` |

The answers differ in **83 of 100 cells**. Nevertheless, `lesson_identifiable` returns `[]` for these three Racket-labeled demonstrations and query. The rival is absent from `LESSON_COMPETITORS`. This reproduces ambiguity for a concrete sequence of four consecutive default draws; no claim is made that the public episode materializer was separately exercised. [Full arrays and hook result](checks/audit/8e6c44aee812/evidence.json)

### Source and execution evidence

The selected target’s `generator.py`, notes, and canonical record were inspected. Its task-local `evidence/review_index.json` is absent; no historical approval inference was made.

- Generator SHA-256: `2d84a82e98f71ec383d8c2ca1c6503d37c00459560ed221899201dccf3c46df6`.
- Selected canonical program-text SHA-256: `0b1d6a0bf93a332b043f577de96fba55af7fcee101e320915fa5d95714233140`.
- Public executed-rule hash: `2f49d92711a1`, with `rule_hash_matches_catalog: true`.
- Public executor’s rule-text SHA-256: `edc8f42a109e447a9a310c67aa8273e12503f7e50a0b98c1848c97a04c6c33ef`; this is retained separately from the raw canonical program-text hash.

One supported public application labeled **eight inputs**: four canonical and four generated. It completed with **exit 0**, all outputs valid, no execution errors, and unchanged generator bytes. The exact command, argument vector, launch directory, effective payload directory, environment, source bindings, and validator results are retained in [evidence.json](checks/audit/8e6c44aee812/evidence.json). The [public Racket receipt](checks/audit/8e6c44aee812/racket.json), [console log](checks/audit/8e6c44aee812/apply.log), [input batch](checks/audit/8e6c44aee812/input.json), and [reproduction script](checks/audit/8e6c44aee812/reproduce.py) are included.

Recommended follow-up: add this rival and distinguish separated reappearances of a color from contiguous repeated bands in the teaching schedule. In this source, those two mechanisms share `complex_repeat`, allowing demonstrations of one mechanism to precede a query requiring the other. This focused audit establishes the reproduced shortcut gap; it does not claim a corpus-wide failure rate or a wrong-label defect. No target source or repository metadata was edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-35316dedd6e945e7-v0001/audit_assets.json), manifest SHA-256 `30139cc580e891201d2d4b597c635339fdda2667f9255d913dc590dc64701a5e`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `9bbefffc3281331b8a02b792ecd9475970e6d8f1b477f359e0bef94858901437`.

# Decisions — review-2ce1eb0bfd0d6744

## Authority, scope, and original intent

The selected repair is `8e6c44aee812` (ARC `539a4f51`), imported version 3.0.0.
The original rationale is documented in its generator: teach periodic nested-L
continuation while independently exposing active period, optional zero padding,
and repeated-color pattern. The selected Racket program already implements the
canonical transformation. It was not changed, nor were shared helpers, catalog
entries, assignment contracts, frozen baseline files, or either audit target.

The final generator is version 3.1.0, SHA-256
`9bbefffc3281331b8a02b792ecd9475970e6d8f1b477f359e0bef94858901437`.
Racket authority remains `2f49d92711a1`, with canonical program-text SHA-256
`0b1d6a0bf93a332b043f577de96fba55af7fcee101e320915fa5d95714233140`.
The executor's callable-text SHA-256 is
`edc8f42a109e447a9a310c67aa8273e12503f7e50a0b98c1848c97a04c6c33ef`;
these two text hashes describe different representations of the same selected
authority and are not interchangeable.

## M1 — Reject silent scalar coercion without shrinking legal seeds

The before battery recorded 51 scalar-contract warnings. The focused baseline
regressions recorded 37 failures and 238 passes: Boolean, float, string, and
other malformed controls were coerced or accepted. Local validation now checks
literal integer seed/index arguments before `gen_ctx` and exact period overrides
before the shared draw helpers. Signed and arbitrarily large integer seeds stay
legal; indices are nonnegative. `period=None` keeps the established default.

Changing the shared helpers would exceed this assignment and could alter other
generators. Restricting seeds to nonnegative machine integers would also change
the existing legal API without solving the actual coercion defect. Both options
were rejected. Evidence: `checks/before/`, `checks/scalar-before.log`, and the
task-owned scalar tests, which include all 144 exact axis combinations across
the three named bands and the default band.

## M2 — Replay the old first-run finding and repair whole lessons

The current-source unresolved audit in
`repo/generators/8e6c44aee812/counterexamples/review-35316dedd6e945e7-v0001/retained/`
was a lead, not a claim assumed to be true. Its seed 0/easy lesson at indices
5..8 was reexecuted as exact saved grids using public `Catalog.apply`.
Keeping only a color's first full contiguous run fits all four canonical pairs
and the three demonstrations, but disagrees on 83/100 query cells. All labels
are correct; the lesson fails to distinguish a plausible wrong rule.

The first candidate declared that rival, introduced separated repeats into both
prefix and complex families, and increased demonstrations from three to five.
Forcing all colors distinct, deleting contiguous repetitions, or silently
resampling the query would hide useful input support or alter the intended
assembly contract. Those alternatives were rejected.

## M3 — Reverse the first repair's incomplete witness design

The intermediate generator SHA
`4b601e6cb5789d1fbb9b3b4497ec8c3ae91e351d54ff1c1c2c7bb47991814da9`
passed its 303 tests, twelve-stage battery, 300-lesson census, and fixed-seed
schedule enumeration. Those checks covered its then-declared rivals. Independent
review found a canonical-fitting variant that preserved all runs of the first
diagonal color while dropping later runs of other colors. It fits five demos
but differs in 128/144 cells on ordinary seed 1/easy/indices 6..11, and 148/196
cells on the seed 0/easy/indices 0..5 population with index 2 held out.
The old hook returned no warning in both cases. The exact reference receipt and
successful reproduction are preserved in `checks/intermediate-shortcut/`.

The final repair declares both this rival and its symmetric color-role variant.
It retains five demonstrations and one query, using two rich complex witnesses
in every six consecutive default draws. Each rich witness repeats both the
first color and another color in separate runs. A separated prefix witness
provides additional evidence against the original first-run rival. This is a
distribution repair accompanied by executable coverage checks, not merely a
new warning string.

## Lesson construction and query policy

At a fixed seed, the pattern cadence has period six. At seed parity zero it is:

| Index modulo 6 | Default pattern family |
| --- | --- |
| 0 | Distinct |
| 1 | Contiguous prefix run |
| 2 | Complex: separated repeats of first and later colors |
| 3 | Contiguous complex repeat |
| 4 | Prefix run with separated first-color repeat |
| 5 | Complex: separated repeats of first and later colors |

Odd seed parity swaps the distinct/contiguous-complex slots and the two prefix
subfamilies. Padding still alternates; periods still follow 4, 5, and two
difficulty-scaled draws in 6..9. Their combined declared period is twelve.
The production lesson takes five consecutive demonstrations followed by one
query from the same family seed. Required rotation checks hold out each of
those six materialized pairs in turn, retaining the order of the other five.
Arbitrary separately drawn or forcibly overridden grids have no such guarantee.

Every six-pair window has two rich witnesses, three examples of each padding
mode, and at least two canonical-size and two generalized-size inputs. A single
holdout therefore preserves those branches and both color-role refutations.
For the original first-run rival, a period-four `ABAB` example is answer-equivalent
to `AB`; at most one of the two rich witnesses has period four. The separated
prefix witness plus the other rich witness give two actual refutations before
holdout. The task probe checks outputs against Racket, not just these structural
counts. Finite coverage is not a proof against every possible hypothesis.

The old requirement to show all three named pattern classes in each lesson was
replaced by actual rival refutation. Distinct examples remain in global support.
Both contiguous and separated repetition families occur with both padding choices
over the checked seeds 0 and 1. Tests explicitly verify `ABAB` answer equivalence
so a syntactic repeat cannot masquerade as a rival disagreement.

### M5 — Remove an unnecessary teaching-domain expansion

The second candidate, SHA-256
`b09cbdc13c22b4150b492bfb799a7a85887fb3a60378b80a39086dd64c5d16f2`,
admitted contiguous two-run `AABB`. All 312 task tests passed, but its final
battery was 11/12: the generic minimal-impostor detector reported acceptance
of solid 2x2 probes in 3/6 cases. That geometry is a valid nested-L staircase
under Racket, as the four-case reference check confirms; the warning does not
show a wrong label. The shared detector has no applicable task-level waiver.

I rechecked the construction and found the expansion unnecessary. Contiguous
complex examples already occur with padding one at seed 1/index 6 and with
padding none at seed 0/index 3, across all bands. Restoring the original
three-run minimum preserves that useful global family support and avoids
introducing a two-block teaching branch. Every period-four complex draw now
uses rich `ABAB`, so exact axis support and the two mandatory rich witnesses
remain. Some windows receive a third rich witness instead of a contiguous
complex example; contiguous complex is a global, not per-window, guarantee.

The warning and the assertion demonstrating the reversal are retained in
`checks/after-v2/` and `checks/short-complex-v2-reversal.log`. The final reference
test still labels `AABB` correctly while checking that the teaching validator
rejects it. No shared linter, canonical data, or permission rule was changed.
All source-bound required checks were rerun after this revision.

## M4 — Portable task tests and reusable evidence

The isolated task-test run initially lacked pytest; this was correctly reported
as infrastructure failure and was resolved in a fresh local Python environment.
The subsequent baseline run had one failing and eleven passing tests: an
inherited, task-owned test used a stale fixed-depth path to canonical data.
That editable task test was migrated to public `reviewer_support` and `Catalog`
interfaces. No immutable baseline or root frozen test fixture was changed.
The original determinism, purity, exact-authority, invalid-input, override,
strict-support, diversity, and recombination assertions were retained. The
same Racket closure is still checked with an A–B–A sequence for mutation/reentry.

The task-owned recurrence probe refuses to overwrite evidence, binds source and
rule hashes, loads old grids directly, iterates actual rival declarations, and
tests whole lessons. A second compact task-owned fixture retains both newly
discovered five-demo ambiguities and has an independent-rival regression test.
These tools are included for future reviewers. Failure and intermediate reports
remain in the return, even where their filenames contain the word `final`.
`RESULTS.json` identifies the source phase for every claimed result.

## Scope of results and remaining decisions

The final public census materialized 300 lessons, 100 per band, with 1,800
pair occurrences and 1,548 unique input grids. All 300 production and 1,800
rotated lessons had zero declared-rival ambiguities and no scoring, materialization,
or hook errors. Fixed-seed enumeration covered starts 0..11 in all three bands:
36 overlapping production lessons, 216 rotations, and 33 unique inputs. These
are different populations and their unique-input counts must not be added.
Source-bound receipts and exact seeds are in `checks/final/lesson-census.json` and
`checks/final/schedule-census.json`.

No model training or Qwen accuracy experiment was run. The separate blind solve
and exposed post-repair solve retain visible-check feedback only; hidden-query
correctness is unknown until independent scoring. Audit targets were inspected
without patching their sources. The imported audit index remains unchanged;
the maintainer can explicitly resolve the repaired first-run finding after
acceptance while retaining unrelated findings. A passing review does not approve
the generator for training automatically.

## Final handoff gate

The exact builder-generated patch was checked and applied to a fresh original
extraction with Git rooted at its `WORK` directory. Every changed and new file
matched its expected bytes before and after all 312 focused tests passed in the
independently prepared Python and Racket environment. This closes the final
replay gate; the acceptance disposition is routine. The full 12-stage battery
and lesson censuses remain the recorded final-source runs, and were not
misrepresented as freshly repeated during this focused replay.

## 2026-10-23 — Proposed episode-level output-scale extension

A separate task-local prototype now varies one executed rule parameter,
`output_scale`, over the bounded values `{2, 3}`. The canonical/default value is
`2`; production `generator.py` and the selected rule hash `2f49d92711a1` are
unchanged. Both settings retain the original reasoning: read the main diagonal,
remove optional trailing-zero padding, recover the active period, and continue
nested-L bands with `active[max(row, col) modulo period]`. Only the output extent
changes from `2h × 2w` to `3h × 3w`. Since lawful inputs are at most 10×10, the
alternative remains within ARC's 30×30 limit.

`workspace/parametric/prototype.py` fixes the selected scale once per complete
episode and exposes independent demonstration/query counts. The retained scale-2
and scale-3 episodes each contain five demonstrations and four distinct queries.
Their public projections omit hidden settings, seeds, programs, metadata, and
query answers; public directory names are SHA-256 IDs of the exact visible bytes.
The lesson check uses only demonstrations plus each query input. A rival is an
ambiguity only when it survives all demonstrations and would change that query's
answer; answer-equivalent alternatives are not counted.

The exact verifier retained at
`checks/parametric/8e6c44aee812-output-scale-v1/report.json` executes both Racket
programs, checks every stored label, replays all canonical labels at scale 2,
and records 18 unique generated inputs. It also applies both programs to the same
lawful 5×5 canonical input: scale 2 produces 10×10 and scale 3 produces 15×15,
with both Racket outputs matching the independent Python mirror. The retained
five-demo lessons reject the alternate scale and the declared tiling, row-only,
column-only, terminal-zero, deduplication, first-run, and fixed-period-four
shortcuts before query answers are revealed.

Prototype source SHA-256 is
`40732203267bd96770e8bf99302c9317aa8dda771901c59631c583c215ab3d13`;
verifier SHA-256 is
`e832edb83e9dbf0d473b9935ac857b50a43371f55e2c72f2d3eeaaa2427be1ca`.
The final selected-task run passed 318 tests. Evidence is bounded to one retained
episode per setting and a finite rival set; this proposed extension is not a
production selection, approval, or training admission.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/8e6c44aee812/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
