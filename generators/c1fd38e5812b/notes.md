# Working notes: c1fd38e5812b

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current review: review-6b2d9c5f5556bcb0

### Authority and scope

Production `generator.py` remains imported version `3.0.0`, SHA-256
`836fa3a06d55f5a6450ccf989f8187695e6f45d8ef81f0a6a384a853a73409af`.
The Catalog authority is rule `0805714fcf25`, exact text
`(rule! (compress-grid g))`. Compression removes consecutive duplicate whole
rows, then consecutive duplicate whole columns. The generator's boundary-sampling
Python solver is equivalent on its exact-expansion grammar; this is not an
assertion of equivalence on arbitrary grids. The module's older `RULE_HASH`
literal `dc8aa1222f34` still differs from Catalog authority. No approval or rule
metadata was rewritten to hide that mismatch.

The recovery manifest mentioned below is absent from this rotating packet.
Its code could not be reviewed or reused here. This review builds an adjacent,
self-contained prototype and preserves the old note as provenance, not as proof.

### Executable family and decisions

`workspace/parametric/promotion.json` declares two values of `view`. The default
`compressed` returns the exact canonical source bytes. The alternative
`largest_component_crop` computes the logical grid, discovers all monochrome
four-connected components including color zero, ranks by logical cell count,
breaks size ties by `(top, left, bottom, right)` and then color, and crops the
original logical grid. Interior colors survive; the output is not a painted or
masked component. Normalization matters because expanded pixel area can rank
components differently from logical cell area. Connectivity also changes the
component census and hence the selected crop.

Counts are independent: 3–6 demonstrations (default 3), 1–4 queries (default 4).
Both settings and all supported counts share a deterministic six-demo/four-query
input bank, sliced only after construction. The separate prototype grammar has
2–10 logical rows/columns, spans 2–12, at least four colors, and physical size
4–30 on each axis. It retains visible first-axis boundaries and exact Cartesian
expansion. Mixed uniform/nonuniform axes, repeated nonconsecutive rows/columns,
black components, holes, irregular objects, equal-area ties, and logical versus
pixel-area selection disagreements are deliberate teaching cases. Seed zero retains the
literal 4×4 minimum query. Other seeds vary the first query; the fourth query
has a substantive 10×10 logical scene expanded to 30×30.

An independent adversarial audit found an actual defect in the first draft:
on seed zero, a rival that breaks size ties by lowest color fit all three demos,
then disagreed on the first query. Fourteen protected Racket evaluations retain
the original lesson and exact programs in
`checks/c1fd38e5812b/tie-color-before/reproduction.json`. The repair teaches
opposite color orderings across two tied-component demonstrations, retaining
three demos and the original minimum query.

A second supported defect appeared after that repair: choosing the bbox-first
component larger than one logical cell fit seed zero's three demonstrations and
failed query index two. Another fourteen protected executions retain that exact
lesson in `checks/c1fd38e5812b/first-nontrivial-before/reproduction.json`.
An earlier two-cell distractor in the physical-area demonstration teaches size
ranking without increasing the demo count. The final bounded registry contains
19 executable rivals, including the first-nontrivial rule and both conditional
color tie breaks. Its results establish only the tested finite distinctions,
not universal rule uniqueness.

The audit additionally constructs a deliberately weakened lesson by uniformly
expanding three logical demonstrations. This hides the difference between
logical and pixel area. A nonuniform query exposes that difference, and replacing
one demo by its original nonuniform expansion teaches the distinction without
adding demonstrations. This research witness is private evidence, separate from
the supervised exporter and separate from the actual first-draft tie failure.

### Assigned shortcut question

The strongest directly supported canonical shortcut is conditional coupled-axis
sampling: use the true row starts, but when row runs are uniform, assume every
column has the first column run's width. It fits all four canonical training
demonstrations. The exact distinguishing input expands
`[[0,1],[2,2],[3,3],[0,1],[2,2],[3,3]]` with row spans `[2,2,2,2,2,2]` and column
spans `[4,8]`, giving a 12×12 grid. Canonical compression returns that six-by-two
logical grid. The rival returns
`[[0,1,1],[2,2,2],[3,3,3],[0,1,1],[2,2,2],[3,3,3]]`.
`checks/c1fd38e5812b/canonical-shortcut.json` retains the complete literal input,
programs, all demonstration outputs, the validator result, and ten protected
Racket executions. Rival fitting is decided from demonstrations before the
witness. The production validator accepts this handcrafted input, but its
current constructor couples the axes' uniformity and does not emit this mixed
regime. This review did not run a new production sampling census. The proposed
family deliberately emits and teaches both mixed-axis regimes; no claim is made
that it samples this exact historical literal input.

### Existing test repair and unresolved production findings

The existing generator test module used a fixed-depth root and a generated
compatibility namespace unavailable in a portable snapshot. It now uses
`reviewer_support` to locate the selected source and canonical data. The two
affected canonical/source tests pass both in the packet and in a fresh native
isolated snapshot, whose import preflight reports no diagnostics. The other
11 original tests, including large draw campaigns, were not rerun. The reusable
`checks/portable_focused_test.py` retains the exact selected source mappings,
test command and result without returning a runtime copy.

The old review-index findings remain owner-controlled: production's coupled-axis
coverage gap and the historical rule-pin mismatch are unresolved. The portable
test failure has a narrow implemented repair, but this review does not formally
clear prior audits. The prototype's broader grammar is a separate proposal and
does not silently repair production generation.

### Handoff and limits

Native qualification, its execution record, the source inventory, public/private
examples and the protected causal replay are the authoritative current check
artifacts linked from `RESULTS.json`. Public IDs derive solely from exact visible
bytes. Controller examples retain four queries privately; actor files expose
one query at a time with no total-count or final-turn hint. Export rejects bad
numeric types, private-field leakage, duplicate inputs and duplicate payloads.

The next owner action is to inspect the proposal, integrate the exact selected
bytes, then run native qualification and fresh acceptance against that integrated
source. Reviewer readiness is not owner acceptance or training admission. The
reported finite tests, seeds and rivals do not prove all-seed sampler success or
unique learnability against arbitrary programs. Production-wide batteries and
unrelated canonical behavior were outside this change's verification scope.


## Current recovery proposal

Unselected hash-bound source repair/prototype proposal: `generators/c1fd38e5812b/workspace/proposals/recovery-c3aa3c66ffc77348/manifest.json`. Original assignment/draw contracts are absent; no source/variant/training approval is granted. Isolated patch replay passed; author checks are reported or incomplete. Reproduce identity or independently rebase/review before selecting these bytes.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/c1fd38e5812b/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
