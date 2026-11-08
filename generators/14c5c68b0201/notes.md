# Working notes: 14c5c68b0201

Current decision: keep the approved generator and canonical `both`-axis Racket
rule unchanged. A separate **proposed/unapproved** prototype under
`workspace/parametric/` adds one episode-wide rule parameter,
`tiling_axes = both | horizontal | vertical`. The alternatives preserve stamp
extraction, colors, containing holes, and stamp-origin phase; they stop expansion
on one axis rather than changing scene decoration.

The retained design uses 3 demonstrations and 4 distinct queries per setting.
Inputs are generated independently of the hidden setting and require every stamp
bbox to be strictly smaller than its hole on both axes. Exact Racket labels show
that demonstrations refute both rivals for every retained query. Public IDs hash
only visible demonstrations and query inputs; private metadata and query answers
are excluded. Batch evidence is sorted by public ID and rejects duplicate visible
payloads or identifier collisions before writing public files.

Limits: this is bounded evidence for the declared three settings and selected
seeds, not production approval, canonical replacement, or training admission.
The existing task test wrapper is blocked in this packet by missing
`scripts.canonical_profile_gate`; the task-local Racket-backed suite is retained
separately. Next useful action is an independent semantic review of whether the
one-axis variants are valuable enough to enter the normal approval pipeline.
The retained verifier also reconstructs canonical public bytes and rejects rule
paths outside the evidence tree instead of trusting manifest metadata alone.

## Native promotion candidate — review-cc3ddb4dcb386aae

The current candidate adds a root native adapter and bounded contract around
the retained `tiling_axes` programs. The exact canonical default, alternate
program definitions and approved production generator are unchanged. Independent
split/index random streams fix the old standalone sampler's query shift when
demonstration counts change. Native limits are 2–6 demos and 1–4 queries, default
3/4, with strict integer seeds and exact setting keys.

Two constructive 8×10 and 12×16 demonstrations teach phase, non-2×2 periods,
multiple holes and both backgrounds without increasing the minimum demo count.
They refute eleven finite Python-defined rivals for both/vertical expansion and
ten for horizontal expansion. Four distinct query
profiles include freshly constructed 24×24 and 30×30 scenes, using two separated
holes and sparse stamps across the full canvas. The 30×30 holes cover 288 cells;
the remaining 612 background cells maintain the canonical modal-background rule.

The 38 new focused tests passed, including independent hand-derived labels and
a grid-only oracle. The reusable native probe passed 12/12 episodes at seeds 0/17,
all settings, demo counts 2/6 and four queries, with 96 protected-Racket labels.
The literal 8×10 phase counterexample changes 11 cells. Public IDs hash visible
bytes only; actor projections contain one query and preserve first-turn content
under single-query use. Duplicate visible payloads fail before publication.

A final self-review exposed a missing period-height witness in the initial
two-demo design: both examples used three-row stamps. An executable fixed-height
three-row rival fit both demonstrations and disagreed on the seed-0 two-row
query. Six protected Racket evaluations retain the original lesson and both
answers in `checks/14c5c68b0201/fixed-height-before.json`; two regression cases
failed before repair. The first demonstration now uses the independent 2×3
motif, while the second retains 3×4/3×5 motifs. The new fixed-height rival is
explicitly refuted, with Racket/Python parity, under both affected settings.
No extra demonstration is needed. The post-repair inventory, qualification and
witness replace their initial source bindings; earlier evidence is kept separate.

Sequential dependency: recover each stamp's pattern, bounds, dimensions, phase
origin and containing hole → compute modulo indices and paint the corresponding
positions inside that hole. A native witness on canonical `both` episodes
substitutes the hole origin for the recovered stamp origin and replays changed
outputs. One-axis Python phase rivals are finite alternatives; their definitions
are not identified with that Racket substitution. Source-bound qualification and
causal replay are the reviewer handoff; the owner must freshly qualify and accept
the exact integrated source. No training admission is claimed. The historical
full task-wrapper limitation above was not rerun; the native adapter and its
changed behavior use their own focused suites and qualification.
