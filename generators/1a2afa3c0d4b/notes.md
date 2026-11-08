# Current working notes: 1a2afa3c0d4b

Version 4.0.0. The unchanged canonical Racket program is the label authority;
`RULE_HASH = 04089d4dac06`. Earlier implementation rationale was not recorded
in the imported placeholder notes; the prior `SUMMARY.md` incorrectly
described the header as fixed at column zero.

## Intended rule and constructive domain

Split the body into three square panels A, B, C at exactly two full color-8
separator columns. Infer the unique exact-color dihedral transform mapping A
to B, apply it to C, and recolor every nonzero cell to the first nonzero color
in the header. Preserve zero. All eight rotations/reflections and header
colors 1..9, including 8, are supported.

The constructed domain uses side 3..9 square panels, foreground colors other
than separator 8, and a unique exact A-to-B transform. Ordinary C is nonempty
and support-asymmetric. Validation also accepts empty C, disconnected shapes,
and additional header cells where these preconditions hold. This validator
does not characterize every input the Racket program could execute.

## Decisions and reversals

- Corrected r3/atr coordinate mappings: both previously returned transpose,
  making the eight-orientation test impossible. Removed the fixed-L fallback.
  Independent NumPy regressions and a literal Racket-verified counterexample
  cover the correction.
- Replaced independent random pixels with connected random supports and
  connected color territories. This reduces fragmentation while preserving
  varied silhouettes and exact-color orbit eight. There is still bounded
  rejection (128 trials), followed by an explicit error rather than a motif.
- Geometry A uses asymmetric support. Color-only A has full support and two
  asymmetric color territories, so silhouette-only inference fails.
- Replaced inert palette/texture axes with observable controls:
  side 3..9, all eight transforms, header color 1..9, header position
  first/interior/last, and A mode geometry/color. Defaults vary by difficulty;
  explicit legal controls are global. Unknown keys and lossy numeric inputs
  fail explicitly. No declared joint incompatibilities are needed.
- Four-slot default schedule: canonical, color witness, broad, color witness.
  Canonical slots retain side 4, monochrome A/C, and first-position header.
  Broad slots allow all transforms, both A modes, and varied positions/colors.
- Witness slots use an unshown nonidentity transform, shifted header, full
  color-only A, C colors excluding the target, and effective header decoys.
  The initial three-distinct-color header made the target its median; replaced
  it with five distinct colors putting the target at rank two or four.
  Every default witness refutes last/minimum/maximum/median header choices.
- Removed the metadata-based validator bypass. Actual malformed input remains
  invalid even when metadata describes a degenerate texture.

## Teaching contract and limits

Three demonstrations and one query are the measured lesson format.
Every four consecutive default slots contain two effective color witnesses.
Holding out any one pair leaves a witness for the nine declared competitors:
binary transform, canonical-only transform subset, column-zero header, last,
minimum, maximum, median header, identity query, and no recoloring. The first
seven fit all three usable canonical labelled pairs; the last two do not.

Final evidence: 12/12 battery stages green; 40 portable task tests; 53 independent
NumPy/Racket comparisons; 31,230 override draws; 300 lessons and 1,200 rotations
without declared-rival ambiguity. Separate seed-101 enumeration covers all four
starting residues in all bands (12 lessons, 48 rotations, 17 unique inputs).
A 450-draw probe measures median object count 12 vs canonical 6 and observes
225/225 default witnesses refuting all nine rivals.

These are finite, source-bound checks, not a proof against all possible rules.
Explicit overrides can remove witnesses, including header endpoint/last-position
or identity-transform requests. Multi-query assemblies are not certified.
Connected ordinary emission support is deliberate; conditional rank heuristics,
arbitrary morphology, and the complete Racket execution domain are not covered.

## Evidence and open findings

The return's `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, and
`checks/` contain the complete receipts and failed iterations. Minimal
Racket-verified inputs are in `counterexamples/`; reusable independent probes
are in `workspace/`, and focused behavioral tests are in `tests/`.

No unresolved main-task blocking finding remains after the final battery.
Training approval remains a catalog/maintainer decision; this review does not
change it. Audits of other tasks are findings-only in the return's `AUDIT.md`.
## Current reviewer considerations

Source SHA-256: `554840ba44d1014d78f49f6e82ca02d80347dd538144c8b919da127fde35ea42`.

# Generator decisions — 1a2afa3c0d4b

## Current source and evidence scope

Final version: `4.0.0`.
Final generator SHA-256: `554840ba44d1014d78f49f6e82ca02d80347dd538144c8b919da127fde35ea42`.
Canonical program SHA-256: `04089d4dac06eaccca48731591120219bf9938aeddad74c372f18cb615855cf5`.
Executed callable-text SHA-256: `ac3e3c0be93388f6a401198d20111219b568ac2a47cdf52353ace6dcda35bb74`.

The existing Racket authority remains unchanged. It reads the first nonzero header value, splits the remaining rows at full color-8 separator columns, chooses the first exact-color A-to-B transform in its declared order, transforms C, and recolors occupied cells. Python predictions and NumPy geometry checks are diagnostics; saved reference labels come from the supported Racket runtime.

The final evidence population is separated from earlier repairs and failures. In particular, `checks/verified-battery/`, `checks/verified-lessons.json`, and `checks/reference-final/` bind the earlier `6b4598…` source; they must not be presented as final `554840…` evidence. Earlier premature names containing “final” do not establish final-source identity. Current evidence uses `ready-battery`, `task-tests-ready`, `reference-ready`, `density-ready`, `ready-lessons.json`, and `ready-schedule.json`.

## Decisions and reversals

| Area | Earlier design and original rationale | Decision or reversal | Why this choice is justified | Evidence |
|---|---|---|---|---|
| Transform implementation | The inherited source intended eight distinct forms. Why its r3 and anti-transpose formulas were written with cancelling index reversals is unknown. Both actually reduced to transpose. | Implement all eight transforms correctly, including explicit identity; retain authority order `id,r1,r2,r3,fh,fv,tr,atr`. | Exact form diversity is a precondition for unambiguous inference. Correcting the branches removes a real generation defect without changing the rule. | `checks/repair-rivals/initial-source.json`; final `checks/reference-ready/report.json`; portable task tests. |
| Asymmetric-panel fallback | Inherited comments called the fixed L a guaranteed-asymmetric fallback; the rationale for silently substituting a fixed motif after 80 failed trials is not otherwise known. | Remove fixed fallback. Use bounded construction/redraw, and raise after 128 unsuccessful trials. | Broken enumeration made every random trial fail, so the fallback collapsed A diversity. A failure must be observable rather than silently becoming a fixed pattern. | Baseline generator source; `checks/density-diagnosis/6b-experiment-summary.json`; final density/support census. |
| Random panel texture | An intermediate repaired sampler used independent occupancy and per-cell foreground-color draws to broaden pattern diversity. | Grow random connected supports and assign each foreground color by connected territorial growth. Color-only A still uses full support. | Canonical panels are connected glyphs. Independent pixels produced excessive same-color fragmentation, not a new rule branch. Connected regions preserve many shapes and exact-color cues while restoring visual resemblance. | Intermediate `checks/verified-battery/checks/1a2afa3c0d4b_after_defect_lint.log`; `checks/density-ready/report.json`. |
| Color-only A | Inherited fixed-L A had an asymmetric occupancy mask, letting binary inference recover every emitted relation; the absence of color-only witnesses was not justified in inherited notes. | Add full-support A with at least two connected color territories and exact orbit 8. | All canonical A/B pairs use one color, so only a deliberate symmetric-support example teaches that foreground identities determine the transform. | `checks/repair-rivals/input.json`, `racket.json`, `report.json`; final 225 default witness checks. |
| C support | Earlier randomized C could accidentally hide transform differences through support symmetry or be empty. | Ordinary C is nonempty and has support orbit 8. Its colors occupy connected territories. | Distinct transforms must give different output geometry in teaching examples; otherwise a wrong inferred transform can agree by accident. | 450/450 final C support-orbit checks; 48 generated NumPy/Racket cases in `reference-ready`. |
| Palette and recoloring | Inherited sampling excluded header color 8 and randomized small panel palettes. A general semantic reason to exclude 8 from the header is unknown. | Permit every nonzero header color, including 8. Panel colors exclude separator color 8. Default witness panel colors exclude every header color; broad/canonical slots permit lawful header/panel aliases. | Header 8 is legal under the authority. Excluding 8 from panels prevents accidental separators. Absent witness header colors force recoloring; aliases in other slots avoid teaching absence as a universal role rule. | `checks/reference-ready/report.json`; final task tests and override gate; final generator comments. |
| Canonical slots | The inherited generator varied shape but did not reserve a canonical-oriented semantic profile. | Every fourth position uses side 4, geometry-mode A, first-position header and small palettes; all eight transforms remain possible. | A recognizable canonical subpopulation supports the original task while interleaved witnesses teach its broader exact-color behavior. These are random glyphs, not copies of canonical arrays. | Final profile-floor/distribution stages in `checks/ready-battery/`; schedule source and census. |
| Broad slots | Earlier repair relied on unrestricted random content everywhere. | Position 2 modulo 4 varies side by difficulty, either A mode, all transforms and header positions, with lawful color aliases. | This maintains shape, geometry, palette and transform variation beyond the targeted witnesses and canonical-oriented slots. | Final density support diversity; override and diversity stages; `reference-ready`. |
| Witness schedule | Earlier random branch selection did not guarantee that each lesson included a color-disambiguating pair. | Positions 1 and 3 modulo 4 are default color witnesses; period is explicitly declared as 4. | Any consecutive three-pair demonstration window contains a witness. A four-pair window contains two, so withholding one pair retains a refuting example. Actual materialized lessons must still be checked because rejection/skips can affect accepted indices. | `checks/ready-lessons.json`; exhaustive fixed-seed start/rotation census `checks/ready-schedule.json`. |
| Header position | Inherited row-0 column-0 header made the column-zero shortcut agree with all generated cases; original restriction rationale is unknown. | Default witness headers start in an interior column; canonical slots start at column 0; broad slots can use first/interior/last. | This teaches the first nonzero value rather than a fixed cell while retaining canonical layouts and exact overrides. | `first_header_cell` canonical-fit and refutation records; `reference-ready` position checks. |
| Header decoys | Intermediate three-color witnesses bracketed the target numerically to refute min/max selection. | Reverse that design: five distinct colors, with first target at sorted rank 2 or 4, then four shuffled later decoys. | Three colors made the target their median. Five colors with rank 2/4 refute minimum, maximum, median and last selection in every default witness. | `checks/review-v2/median-header-review.json` and real Racket counterexample; final median regression and 225 witness comparisons. |
| Header endpoints and last-position overrides | A universal five-color rank witness is impossible for target 1/9 or when the true header is the final cell. | Honor exact overrides and weaken only the impossible witness condition. Endpoint witness headers use fewer decoys; last-position headers have none. | An override must not silently change the requested color/position or raise merely because a teaching property is impossible. Domain lawfulness and default lesson identifiability are separate contracts. | Final task tests, full override matrix and `reference-ready` cases including endpoint colors and last position. |
| Five public axes | Inherited metadata included helpful/degenerate texture names with weakly related or no implemented effects. | Expose the five implemented axes only: side, transform, header color, header position, A mode. Reject unknown keys and invalid values; reject bool/float/string integer overrides. | Declared controls should change the actual construction and accept their advertised domain. Degenerate meta flags must not exempt malformed grids from validation. | Final task tests and override/selfcheck battery stages. |
| Validator limits | Inherited self-check tested little beyond header column 0 and at least two separators, and bypassed checks for certain metadata textures. | Validate integer rectangular grids, exact dimensions for three square panels of side 3..9, a nonzero header, exact separator locations, panel exclusion of 8, and one exact A-to-B transform. Metadata never exempts malformed input. | These conditions establish the selected generator manifold and safe exact inference. Ambiguous A is deliberately outside this generator's accepted manifold even though the authority has a first-match tie policy. | Final malformed-input task tests; selfcheck/mutation battery stage. |
| Legal edges versus ordinary draws | Ordinary teaching draws require nonempty asymmetric C and connected glyphs. | Validator permits lawful empty C, additional header colors and other lawful C supports; it does not require every accepted input to be a sampled teaching witness. | The authority handles these cases. Acceptance must not confuse sampling preferences with rule preconditions. The side-3..9, square-panel domain remains an explicit generator restriction. | `reference-ready`: actual Racket checks for empty C and multiple headers; final self-check implementation. |
| Rival declarations | Initial repair had a small list and missed median header selection. | Declare seven canonical-fitting shortcuts and nine lesson competitors, with dynamic probes reading the live declarations. | Every canonical-shortcut claim must fit all usable canonical pairs. Identity-query and no-recolor are lesson rivals, already refuted canonically, so they are not canonical shortcuts. | `checks/ready-lessons.json` → `canonical_rival_fit`; final density probe dynamically scores all nine. |
| Authority and evidence | Racket was already the selected rule contract. | Do not change Racket, shared runtime or labels to match Python. Keep intermediate defects and source hashes. | The generator should expand and teach the existing task, with executable reference evidence independently checking the implementation. | `reference-ready/authority.json`; authority-sync stage; source-bound failed iterations and median counterexample. |

## Public axes and honest defaults

| Axis | Exact accepted domain | Default sampling choice and reason |
|---|---|---|
| `panel_side` | Integer 3..9 | Canonical slots use 4. Other defaults favor easy 3/4, medium 4/5/6, hard 6/7/8/9. Overrides remain accepted across bands; difficulty is a preference, not a smaller legal domain. |
| `transform` | `id,r1,r2,r3,fh,fv,tr,atr` | Canonical/broad slots use all eight. Default witnesses favor r2/r3/fv/atr to refute the canonical r1/fh/tr-only rival. |
| `header_color` | Integer 1..9, including 8 | Ordinary canonical/broad defaults use all nine. Default witnesses use 2..8 so the target can occupy a nonextreme, nonmedian rank. |
| `header_position` | `first,interior,last` | Canonical first; default witness interior; broad all three. Later decoys require remaining header cells, so the construction reserves sufficient tail space. |
| `a_mode` | `geometry,color` | Canonical geometry; witnesses color; broad either. Geometry support has orbit 8; color-only full support has orbit 1 while exact colors have orbit 8. |

Connected supports and territories are a sampling restriction justified by canonical texture and measured fragmentation, not a claim that disconnected inputs are semantically invalid. Random placement, support size, frontier growth, color seeds and territorial boundaries retain diversity. There is no fixed-template fallback. The final broad sampler still varies all eight transforms and supported dimensions; 450 direct draws yielded 365 unique inputs across bands and 150/150 distinct inputs within each band. Canonical-oriented defaults overlap across difficulty bands, so raw draw counts must not be presented as unique-input counts.

## Teaching contract and limits

The production lesson contract is **three demonstrations and one query**. The declared semantic schedule is `canonical, color_witness, broad, color_witness`, period 4. Default witness A requires exact color inference; C makes transform geometry observable; the shifted five-color header requires positional order rather than numeric rank; absent header colors require recoloring. Each default witness individually refutes all nine declared competitors. This permits arbitrary single-query holdouts of each measured four-pair lesson, not just the original final query position.

The production materializer may skip duplicate or rejected draws. The census therefore records actual accepted sample indices and refuting pairs; schedule arithmetic alone is not the evidence. Fixed-seed enumeration covered every start residue and every single-pair query holdout at seed 101 across the three bands: **12 lessons, 48 rotations, 48 overlapping pair appearances, 17 unique inputs**. Its `complete_fixed_seed` coverage receipt is restricted to that seed and those bands. The broader census materialized **300 lessons** using its recorded hashed seed recipe, 100 per band, with **1,200 unique inputs and 1,200 rotations**. Both production and rotation verdicts are `no_ambiguity_found`, with zero ambiguity, hook warnings or scoring/materialization errors.

These measurements concern the declared rivals and sampled population. They do not establish universal identifiability, exhaust arbitrary random support, or certify every possible accepted-pair rejection schedule. Explicit overrides can remove witness conditions: `id` makes binary inference agree, geometry-only A removes the color cue, r1/fh/tr can agree with the canonical transform subset, and endpoint/last-position headers cannot supply the default rank witness. Such inputs remain lawful; a lesson assembled with arbitrary overrides requires its own identifiability check. The default curriculum's guarantees are not silently extended to those assemblies.

## Final checks and denominators

All rows below bind the final `554840…` generator source. Exact commands, execution directories, runtime manifests and full hashes are retained in the corresponding receipts and `RESULTS.json`.

| Check | Actual result | Population and scope | Evidence |
|---|---|---|---|
| Full after-repair battery | 12/12 stages green; no failed/advisory stages | Includes semantic rotation requirement and the ordinary inherited gates | `checks/ready-battery/checks/1a2afa3c0d4b_after_battery_summary.json` |
| Portable focused task tests | 40/40 passed; no failures/errors/skips | Isolated staged task-test runtime | `checks/task-tests-ready/result.json`, `checks/task-tests-ready/checks/task_tests.xml` |
| Independent NumPy versus actual Racket | 53/53 passed | 48 generated cases = 3 sides × 2 A modes × 8 transforms, all 3 usable canonical pairs, 2 legal edges; header colors 1..9 and all 3 positions | `checks/reference-ready/report.json`, `authority.json`, `command.json` |
| Actual-generator density and witness census | 450 accepted draws, 365 unique overall; object median 12 versus canonical median 6 | Seed and sample index 0..149, 150 per band; no monkeypatch and no new Racket calls | `checks/density-ready/report.json`, `inputs.json` |
| Per-grid default witness refutations | 225/225 for each of 9 rivals; 2,025/2,025 comparisons | The 225 default witness draws in the 450-draw census; task-local Python diagnostic predictions | `checks/density-ready/report.json` |
| Racket-labelled lesson census | 300/300 production lessons and 1,200/1,200 rotations without declared ambiguity | 100 lessons per band; 1,200 unique inputs; remaining demonstrations preserve order | `checks/ready-lessons.json` |
| Fixed-seed schedule enumeration | 12/12 lessons and 48/48 rotations without declared ambiguity; complete coverage | Seed 101, period 4, all 3 bands; 48 overlapping appearances, 17 unique inputs | `checks/ready-schedule.json` |

The density detector uses same-color four-connected components and the entire grid's majority color as its inferred background. Its generated/canonical median threshold is strictly greater than three times the canonical count. Final median 12 is below threshold 18; easy/medium/hard maxima 18/19/20 are reported rather than hidden. Those maxima do not trigger a median-based detector. All 450 exact A orbits and C support orbits were size 8, with geometry and full-support color modes both represented.

## Retained failures and provenance

The baseline counterexample in `checks/repair-rivals/` binds `a1470992…`, not final source. It establishes the binary-versus-exact semantic distinction with actual Racket execution. The authored rival helper initially duplicated a transform in its own diagnostic implementation; its assertion failures and consequent missing-input apply failure are retained in `failed-iterations.json`. Those failures were repaired before its successful authority comparison.

The intermediate three-header median shortcut and fragmentation failure remain in `checks/review-v2/` and `checks/verified-battery/`. The source-bound exploratory texture summary is `checks/density-diagnosis/6b-experiment-summary.json`; it honestly records an in-memory proposal, not actual final code or Racket labels. The intermediate header color-loop variable collision remains in `checks/iterations/header-collision.json` with its source snapshot. These iterations are not counted as final passes.

The earlier finished solve was preserved under `checks/prior-solve/`. A subsequent public solve preparation unexpectedly inherited old attempt/finished-notes files, producing mixed source identities. The full contaminated episode is retained under `checks/solve-reset-failure/`; the external copying cause is unknown, and no causal infrastructure claim is made. Recovery archived those bytes, regenerated the same final-source challenge through public commands, checked a clean revision 1 and finished successfully. No frozen report was renumbered or edited to make the mixed episode appear valid. Root's solve and result records carry the exact recovery commands and hashes.

## Evidence restoration

Evidence paths above name the logical uncompressed files. Where a large JSON is retained as `.json.gz`, use the returned `COMPRESSION-MAP` to restore its exact original path and verify its recorded size/SHA-256 before replay. A compressed source-bound report preserves the same claim; the gzip filename does not represent a different iteration. Compact decisive counterexamples and command receipts remain individually identifiable.
