# Working notes: 27080597d778


## Review review-628cb7ab770997ce, 2026-10-23 — proposed fallback-panel parameter

Production and canonical authority remain unchanged. The selected generator is
still SHA-256 `dc379efc26f48130d6f42e7f52573ca74dfb4eccf407d467b741d94e832c37d9`;
this review adds only a task-local prototype, focused tests, an auditor, and
compact evidence under `workspace/parametric/` and `checks/parametric/`.

The bounded episode-wide parameter is `fallback_panel in {left,right}` with
canonical/default `left`. Both settings keep the same global zero-complement
predicate and successful color-preserving overlay. Only the failed-predicate
branch varies: copy the complete left panel (canonical) or the complete right
panel (proposed). Exact Racket SHA-256 values are
`f42d1fc588c8fbcfc0b1066fa6da031c3678182dd750b7c01a06e470f6211300`
(left) and `ce6dd935c81a5286b11f853deed33222799638e266b91827daaddf23dd4bd63a`
(right).

Each episode fixes one setting for four demonstrations and four queries. Paired
seeds `2k` and `2k+1` share `input_seed=k`, so visible inputs and their shuffled
order are identical while only the hidden rule changes. Every split contains
complement, overlap-only, gap-only, and balanced overlap-plus-gap cases; the
demonstrations reject the opposite declared setting before any query is scored.
All labels come from the bundled protected Racket runtime and are independently
checked by a Python mirror.

Retained evidence:

- `checks/parametric/fallback-panel-final/`: two opaque public challenges,
  private setting/query records, exact rules, and 9/9 canonical replay.
- `checks/parametric/fallback-panel-adversarial.json`: passed export tamper/privacy
  checks and a 72-input / 144-Racket-evaluation matrix, with 18 inputs per branch.
- Focused prototype tests: 17 passed; full assigned generator tests: 135 passed.

The alternative is a proposed extension only: it is not a canonical-rule change,
production API, approval, or training admission. Evidence is bounded to two
settings and a finite input matrix; demonstration identifiability excludes the
opposite declared setting but is not a proof against every conceivable rule.
The next useful action, if the variant is desired, is independent semantic review
of whether right-fallback remains close enough to the source family for admission.

## Review d13c4d75aefa4501, 2026-09-28

The original v1.4.0 generator's XOR invariant excluded the rule's entire fallback
branch. An independent 32-seed × 16-index × 3-band census produced 1,536/1,536
complements; unconditional overlay agreed with every generated label. Four of
nine canonical inputs were rejected by the original checker. The original
summary incorrectly suggested normalizing the output to the left color.

The v2 input distribution constructs a complementary panel pair, then mutates
only the right panel for three contrast classes. Single-fault negatives make the
causal difference small; balanced overlap-plus-gap preserves total occupancy and
refutes a count-only decision. One clean row containing a right-only pixel is
reserved in every ordinary negative, so a row-local rule visibly disagrees with
the global fallback. Geometry is not selected by executing the answer rule.

Four demonstrations, not three, are needed for the chosen contrast set. The
shared public exporter currently does not call `lesson_identifiable`, and its
three-demo default may omit the very case needed to identify a query. The
workspace gate validates the *emitted* demonstrations and **every** query,
independently executes canonical Racket labels, and rejects surviving declared
rivals. Its research exporter shuffles demos and splits private answers/programs
from public challenge JSONL. Shared exporter code and approval metadata are not
changed within this task's scope.

### Input decisions and override compatibility

- Heights default to easy 3..5, medium 4..8, hard 7..10, with independent 40%
  height-4 / canonical-palette anchors in every band. Any explicit height 3..10
  works in every band. The anchor predicate is only a shape/palette support
  check; it is not a complete canonical-manifold certificate.
- Ordinary palettes are distinct non-gray colors. Explicit same-color palettes
  remain legal. Explicit color pins are honored, including a lone right-color
  pin with `palette_kind='same'`.
- Six mask distributions remain. Alternating uses row stripes; checker uses
  a checkerboard. Left/right-heavy are stochastic rather than nearly constant.
  Scattered gets two-thirds of unpinned layout choices to limit texture shortcuts.
- `balance` means a **scattered-mask density hint**, not an exact occupancy count.
  A lone balance pin selects scattered. A balance pin combined with a fixed-
  density/structured layout is rejected with a declared incompatibility rather
  than silently ignored.
- `max_defects` is an upper bound of 1..3, not an exact count. It cannot be pinned
  together with explicit `branch='complement'` (which has zero faults). To make
  a one-edit counterfactual, omit the cap on the complement and set it to 1 on
  the negative; mask/color streams are independent of the cap.
- `texture` remains a layout alias but is not advertised as a second independent
  axis. Lawful empty/full-panel diagnostics are explicit-only. The old inert
  `anchor_endpoints` and `asymmetry_force` controls were retired: v2 rejects them.
  Unknown and malformed overrides fail loudly. v2 does not promise v1 seed replay.

### Verification and remaining limits

All nine canonical pairs and the main distribution census are independently
checked against unchanged Racket. Named semantic rivals include unconditional
crop/overlay, one-sided Boolean checks, total occupancy, row-local and pixel-local
rules, and monochrome recoloring. Root `checks/` in the review response retains
before, failed intermediate, and final battery evidence; regression red/green
logs; real admitted/rejected exports; and parity/metamorphic probes.

A finite rival list can miss another shortcut. The four-profile schedule still
has a periodic index structure, and native unshuffled exports retain a positional
cue; use the workspace shuffling/gate path. Changing the shared exporter to invoke
contracts belongs in a separate repository-level integration. No Qwen training
or held-out ARC accuracy was measured; this remains research-only data.
## Current reviewer considerations

Source SHA-256: `dc379efc26f48130d6f42e7f52573ca74dfb4eccf407d467b741d94e832c37d9`.

# Input and implementation decisions

Assignment: `review-d13c4d75aefa4501`; task: `27080597d778`.
Only the selected generator and its local documentation/tests/workspace change.
Where the old implementation supplies no rationale, that is stated explicitly
rather than inventing one.

## 1. Keep the canonical rule; repair the generator's domain

**Original choice:** only exact XOR-complement inputs were generated and accepted.
The old summary described a simple merge and suggested left-color normalization.
No retained rationale explains ignoring the global fallback; associated notes
were empty. The executable Racket rule and four negative canonical examples make
the omission observable.

**Chosen:** preserve canonical/base bytes and their selected hash; accept and
construct both outcomes. Labels remain Racket-generated. A Python audit predicate
is used only for checks and is independently compared with canonical execution.

**Alternative:** narrow or rewrite the Racket rule to fit the old generator.
Rejected because that would contradict legitimate canonical examples and conceal
the actual distribution bug. Probe: all nine canonical pairs and 1,536 generated
inputs per version, with canonical/archival hash preservation in the return.
Limit: the declared input grammar remains this task's two monochrome panels;
valid general Racket inputs outside that grammar are not promised as samples.

## 2. Four contrast profiles, not only a binary branch label

**Original:** 100% complement over 1,536 draws; unconditional overlay fits all.
**Chosen:** complement, overlap-only, gap-only, equal-count overlap-plus-gap.
Each gets one slot in a seed-permuted four-slot schedule. These distinguish full
complement checking from checking only collisions, only gaps or total occupancy.
The canonical negatives all combine overlap and gap, so the one-sided shortcuts
cannot be ruled out by those canonical examples alone.

**Alternatives:** IID profile sampling may omit a necessary type in a short
lesson. A six-slot schedule with three complements and one of each negative
would balance binary outputs 50/50 but cost six reliable demonstrations. Four
slots are the minimum for this explicitly chosen contrast set, not a theorem
about the task's teaching dimension.

**Probe:** every four-draw window over multiple seeds/start indices and bands;
paired 1,536-draw Racket census; semantic-gate materialized lessons; actual JSONL
admission. Failure mode: each profile is 25%, so fallback is 75% and unconditional
crop has 75% marginal accuracy. Per-lesson falsification, not misleading marginal
accuracy, is the acceptance objective. Regular index schedules can leak position;
final-demo shuffling mitigates that particular cue, and index metadata is removed
from the public challenge view.

## 3. Localized right-panel counterfactuals and a clean row

**Original:** complementary ownership masks only; no causal contrast.
**Chosen:** generate one mask and mutate only right-panel cells. Overlap adds a
right pixel opposite a nonzero left pixel; gap removes a right-only pixel;
balanced applies equal numbers of both. The left panel, colors and geometry
streams are unchanged by a branch override. Preserve a clean row containing a
right-only pixel and reserve eligible cells outside it.

**Alternatives:** regenerate unrelated negative panels, or corrupt arbitrary
cells without the clean-row condition. Both can hide the global-vs-local
causality. Probe: max-defect=1 negatives differ by exactly one pixel (overlap/gap)
or two (balanced); balanced preserves total occupancy; negative labels remain
the left crop and disagree with overlay/row-local rivals. The construction uses
no output-based rejection sampling. Limit: finite localized defects are not an
exhaustive distribution of all non-complementary inputs.

## 4. Heights and canonical support

**Original:** height ranges were tied to difficulty; the hard population lacked
height-4 anchors, and some advertised explicit heights were rejected by narrower
per-band draw bounds. Original rationale beyond size-based difficulty is unknown.

**Chosen:** default bands easy 3..5, medium 4..8, hard 7..10, with independent 40%
height-4 / canonical-palette anchors in every band. All explicit heights 3..10
are accepted regardless of band. Alternative: force all heights to four, losing
size variation; or never anchor hard, reproducing zero support. Probe: all band ×
height endpoints × branch combinations, full override battery and strict anchor
census. Limit: the strict predicate certifies height/palette support only, not a
complete geometric canonical manifold; “hard” is a sampling policy, not measured
human/model difficulty.

## 5. Colors and same-palette behavior

**Original:** panel colors were sometimes drawn outside override provenance;
same-palette cases could ignore a requested pin. The summary's recoloring claim
was inconsistent with Racket. **Chosen:** keyed color draws with values
1,2,3,4,6,7,8,9, excluding background and separator. Default palettes are distinct;
explicit same-color requests remain legal. Equal two-color pins imply same;
a lone right pin plus `palette_kind='same'` fixes both colors. Explicitly
contradictory palette/color pins reject with declared incompatibilities.

**Alternative:** always use canonical blue-left colors; this risks palette
memorization. Or forbid same-color panels, needlessly narrowing legal diagnostic
coverage. Probe: color pins and same palettes, palette permutation metamorphisms,
Racket recoloring-rival witnesses. Limit: monochrome panels are retained as the
source task's grammar; arbitrary multicolor halves are not introduced.

## 6. Mask variation, balance and diagnostic textures

**Original:** six advertised layouts, but alternating duplicated checker and
heavy modes were nearly constant. v1 also accepted inert anchor/asymmetry knobs.
Their intended semantics were not documented. **Chosen:** distinct row stripes
and checker patterns, stochastic heavy layouts, shifted diagonal masks, and
roughly two-thirds scattered unpinned choices. Keep both left/right roles visible
and right-only pixels in at least two rows to support negative witnesses.

`balance` is a scattered density hint, not an exact count. A lone pin chooses
scattered; explicit density hints on fixed patterns reject rather than becoming
inert. Lawful empty/full-panel textures remain explicit diagnostics and are not
advertised as ordinary AXES values. `texture` remains an alias, not an independent
cartesian axis. Obsolete anchor/asymmetry controls reject in v2; replay stability
is promised within v2, not between versions.

**Alternatives:** retain ignored controls for compatibility or inject unrelated
noise to make them “effective”; both mislead callers. Probe: first-after six
inertness findings, eight new red/green regressions, 71,460 final override draws.
Limit: mask labels are distribution families, not exactly recoverable properties;
`observe_overrides` does not invent observations for density/layout hints.

## 7. Defect counts and honest applicability

**Original:** no defect control because all samples were complements.
**Chosen:** `max_defects=1..3` is an upper bound; defaults are one except hard
(three). Geometry can make the feasible count smaller. The count is drawn
independently from the mask stream. Explicit complement + defect cap is rejected
as inapplicable; omit the cap on a positive counterfactual and pin it on negatives.

**Alternative:** an exact defect count would force more geometric retries or
reject small-height cases. An upper bound is more composable, but must be named
and documented honestly. Probe: exact one/two-pixel counterfactuals at cap one,
multiple bands/heights, strict mixed-override battery. Limit: changing an upper
bound need not change every particular draw; claims concern applicability and
behavioral capacity over sweeps, not guaranteed per-seed differences.

## 8. Gate actual final lessons, independently and fail-closed

**Original:** the generator had no semantic hook. Shared export can slice three
demos without consulting a four-demo requirement. **Chosen:** task contracts with
eight named rivals, five witnesses, and query-specific `lesson_identifiable`;
plus a workspace tool that validates actual final private episode JSONL, executes
all labels in Racket and independently recomputes rival survival for every query.
Missing/invalid contracts, malformed grids, duplicate inputs, mutation, source
mismatches, bad labels, invalid rival predictions and executor failures reject.

**Alternatives:** validate only the first query, only fresh raw draws, or trust a
hook's empty result. Regression witnesses show why all three can fail open.
Requiring a fixed minimum demo count would over-reject smaller query-sufficient
lessons, so only the construction policy uses four; the validator tests content.
A surviving rival is harmless when it agrees on the actual query.

**Probe:** 16/16 native three-demo lessons rejected; first-good/later-bad query
witness; 24 actual four-demo lessons and 48 queries rechecked; injected broken
rivals initially passed, then five regressions failed and passed after hardening.
Limit: named rivals are finite and task-owned. Validity and semantic admission
are not a proof of unique induction or a measured Qwen gain. Duplicate-input
rejection is a deliberate data-quality policy, stricter than output validity.

## 9. Public/private separation and source provenance

**Chosen:** independent seeded final-demo shuffling, synchronized sample-index
permutation, public challenges containing only train input/output and test input,
and separate private query labels/full episodes. File and source hashes bind
receipts; output paths are exclusive. Failed builds keep rejected inputs and
reasons but no public challenges or success manifest. Native approval metadata
is unchanged; `--allow-unapproved` is explicit research access.

**Alternative:** serialize full rich episodes as model-visible challenges, leaking
programs/answers/identity. Probe: public-view structure tests, actual exported
files and fresh relocated build/audit. Limits: hashes are staleness/provenance
checks, not signatures; optional sample indices are checked for consistency,
not replayed by the admission gate. The tool is not a shared-exporter patch and
still depends on private runtime helpers, documented for future integration.

## 10. Evidence, scope and stopping criterion

The original draw/baseline were not rerolled. Failed before/after stages, red tests,
rejected lessons and a failed audit hypothesis are retained. Canonical/base rules,
shared source, approval metadata and both audit targets remain byte-identical.
The full repository suite's two transient short-timeout failures are recorded,
with both isolated reruns passing; a clean full-suite result is not asserted.

The scoped work is complete when the final 12-stage battery, 118 task tests,
Racket-backed data/gate checks and exact-patch relocated replay pass, required
reports/audits are present, and the native return validator accepts the compact
bundle. Full-model training, shared pipeline integration, fixing separate audit
targets and proving absence of every possible shortcut are outside this review's
scope and are explicitly not claimed.
