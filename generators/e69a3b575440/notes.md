# Working notes: e69a3b575440

## Current selected implementation

Version `2.0.0`; generator SHA-256
`56d675c33e26030122624b69679f985a087b31e0202999e746c4abca86b1dbc3`.
Canonical Racket authority remains unchanged at rule hash `8710239f76c6`.

The cell at `(0,0)` is a command token. Remove it, crop the single connected
interior object, and apply command 1 identity, 2 clockwise rotation, 3 half
turn, 4 transpose, 5 left/right reflection, 6 up/down reflection, 7 transpose,
or 8 anti-transpose. Commands 4 and 7 are intentionally authority-equivalent.

## Repair in this review

The pinned baseline accepted malformed public-call scalars through Python
coercion: boolean/float/string seeds, boolean/float/string and negative sample
indices, invalid difficulty values, and mistyped declared override values. The
before battery was 11/12 green and `defect_lint` retained 132 strict-scalar
warnings. The repair adds one pre-generation validator that requires exact
integer seed/sample-index types, a nonnegative sample index, the documented
difficulty values, known override names, exact integer override values, and
axis bounds. This is a boundary repair only: generation, Racket semantics, the
schedule, and the sampled distribution are unchanged.

Minimal examples are retained in `counterexamples/strict_call_scalars.json`.
Focused regressions live in `tests/test_strict_call_contract.py`; the imported
baseline `tests/test_generator_e69a3b575440.py` remains byte-for-byte frozen.

## Distribution and teaching decisions

The existing design was retained after remeasurement:

- Sequential sample indices schedule commands 1 through 8 exactly once in each
  eight-demonstration production lesson. This teaches authority-only commands
  5 through 8, which do not appear in the five canonical pairs.
- Objects are one 4-connected component, fill their bounding box, expose at
  least four distinct dihedral views, and visibly distinguish the selected
  transform. Command-1 samples also refute an always-rotate shortcut.
- A difficulty-dependent canonical prior preserves exact canonical-scale support
  while broader draws vary canvas, object size, and one to three object colors.
- Declared exact controls are `grid_h` 7..14, `grid_w` 7..14, `cmd` 1..8, and
  `object_color_count` 1..3. They are observable in returned pixels.

The prior return `local-random-586e0b05d143` was used only as a lead for the
8-command schedule, transform-revealing objects, canonical prior, and the
commands-5..8 authority gap. Every claim above was remeasured against this
packet's pinned source; the prior return was not treated as current evidence.

## Measured final evidence

The final after battery is 12/12 green. The profile floor has 15/60 exact hits
and 19/60 envelope hits, with exact support easy 3/20, medium 5/20, hard 7/20.
The strict semantic census has 148/600 canonical-like draws (24.67%), all eight
command witnesses present in every band, and 12/12 production smoke lessons
identified against the declared rivals. Portable task tests pass 41/41 in the final handoff tree and 41/41 after the
exact task-local patch is applied to a fresh packet extraction. The final
battery, replay, and source hashes are recorded in `RESULTS.json`.

The larger lesson census materialized 300 ordered production lessons (100 per
band), each with eight demonstrations and one query. It found 0/300 ambiguous
production lessons and 0 production hook warnings. Holding out every labelled
pair produced 2,700 query rotations with 0 declared-rival ambiguities but 2,100
hook warnings: when a command's sole demonstration is held out, that query
command has no remaining direct example. Therefore the selected curriculum is
ordered-only; arbitrary query rotation is not supported by this schedule.
Finite declared-rival checks are not a proof of universal identifiability.

## Strongest canonical shortcut

A rule that implements canonical commands 1..4 but treats commands 5..8 as
identity fits all five canonical pairs. The repaired production schedule emits
commands 5..8 deterministically. A command-5 witness at seed 777, sample index
4 is retained in `checks/shortcut-rival/evidence.json`; canonical Racket applies
a left/right reflection while the shortcut returns the unreflected crop.

## Parametric prototype

`workspace/parametric/` contains a proposed episode-level `quarter_turn`
parameter with values `clockwise` (canonical/default) and `counterclockwise`.
Only command 2 varies. Each prototype episode contains an asymmetric command-2
demonstration and query, so the two settings are directly distinguished.
Racket-backed evidence for seeds 7300 and 7302 is in
`checks/parametric/evidence.json`. This prototype is separate from the selected
production generator and does not change canonical authority or approval.

## Known limits and open decisions

- Preserve the eight-demo sequential command schedule unless lesson assembly is
  redesigned to supply redundant per-command evidence; arbitrary holdout rotation
  currently violates the direct-command teaching hook.
- The canonical examples alone do not establish branches 5..8; those branches
  remain justified by the synchronized executable authority and should receive
  maintainer confirmation if canonical visual scope is meant to be narrower.
- The declared rivals cover several strong shortcuts, not every possible solver.
- The parametric quarter-turn extension has two retained seeds and one explicit
  parameter rival; it is research evidence, not production integration.
## Current reviewer considerations

Source SHA-256: `56d675c33e26030122624b69679f985a087b31e0202999e746c4abca86b1dbc3`.

# Distribution and implementation decisions — e69a3b575440

## D1 — reject scalar coercion at the public boundary

**Original choice:** unknown. The pinned implementation delegated call arguments
to `gen_ctx`; Python booleans, floats, strings, and negative indices could reach
keyed generation. The before defect linter reproduced 132 accepted-invalid
scalar cases.

**Decision:** validate before constructing the generation context. Require exact
`int` for `seed` and `sample_index`, require `sample_index >= 0`, enumerate the
four accepted difficulty values, reject unknown axes, and require exact in-range
integers for every declared override.

**Alternatives rejected:** coercing with `int()` preserves silent aliases and
makes provenance misleading; relying only on the shared defect linter leaves the
runtime contract broken; validating after `gen_ctx` allows invalid values to
influence keys before rejection.

**Probes:** retained red/green task-test runs, before/final defect-lint receipts,
and `counterexamples/strict_call_scalars.json`.

**Failure modes and limits:** this is task-local duplication of a contract that
would be better centralized. It deliberately rejects callers that previously
passed coercible values. Lawful generated pixels are unchanged.

## D2 — keep the existing command schedule

**Original rationale:** associated note GNOTE-002169 from
`local-random-586e0b05d143` says independent random commands could omit branches;
sequential residues guarantee full branch teaching. I treated this as a lead and
remeasured it.

**Decision:** keep `cmd = 1 + sample_index mod 8` unless explicitly overridden.
An ordered production lesson has eight demonstrations covering every command,
then a query. This directly counters the strongest canonical shortcut, which
implements commands 1–4 and ignores 5–8.

**Alternatives rejected:** independent random command selection can omit rare
branches; a four-command curriculum would match the visual canonical pairs but
under-teach synchronized authority branches; duplicating every command would
increase lesson size without current downstream evidence.

**Probes:** the semantic gate sees all command residues; 300 production lessons
have no hook warning; `checks/shortcut-rival/evidence.json` supplies an exact
command-5 disagreement.

**Failure modes and limits:** arbitrary query rotation is not supported because
each command appears once. The 2,700-rotation census records 2,100 hook warnings.
A future rotatable curriculum needs redundant command demonstrations or a
query-aware selector; do not infer rotatability from the ordered pass.

## D3 — retain transform-revealing connected objects

**Original rationale:** associated note GNOTE-002170 says symmetric or
disconnected objects hide command behavior. Current code builds one connected,
full-bounding-box object, requires at least four distinct dihedral views, and
requires the selected nonidentity transform to change it.

**Decision:** retain this constructor unchanged. For command 1, require clockwise
rotation to differ so an always-rotate rival is observable. For command 8, avoid
a monochrome 2x2 square by expanding one dimension when necessary.

**Alternatives rejected:** unconstrained Bernoulli masks can create disconnected
islands; symmetric rectangles make multiple commands answer-equivalent; fixed
hand-authored shapes would reduce support and create template shortcuts.

**Probes:** final self-check/semantic/diversity gates, command witness counts over
600 draws, and 300-lesson census.

**Failure modes and limits:** four distinct views do not guarantee all eight D4
operations are distinct; commands 4 and 7 are intentionally identical in the
authority. Finite named rivals do not exhaust possible abstractions.

## D4 — keep a canonical prior plus broader support

**Original rationale:** associated note GNOTE-002171 says the older baseline had
no canonical-profile coverage, while canonical-only templates would lock in
size/palette artifacts.

**Decision:** retain the difficulty priors (easy .70, medium .55, hard .40) on
canonical-scale, one-object-color scenes for commands 1–4, while broader draws
use 7..14 canvases, 1..3 object colors, and difficulty-scaled object sizes.

**Alternatives rejected:** canonical-only sampling overfits dimensions and
monochrome objects; all-broad sampling risks failing support floors and visually
drifting from the source task; changing these rates during a scalar-contract
repair would confound causality.

**Probes:** final profile floor exact 15/60 and envelope 19/60, with exact support
in every band; strict semantic support 148/600.

**Failure modes and limits:** rates are engineering priors, not optimized
training weights. Canonical prior is limited to commands 1–4 because commands
5–8 lack canonical visual pairs. This preserves authority breadth but means
strict-canonical support and full-command support are different populations.

## D5 — leave Racket authority unchanged

**Original rationale:** synchronized canonical and archival sources already
encode all eight branches. No measured mismatch, crash, or grammar issue was
found.

**Decision:** no rule edit. Pin `RULE_HASH = 8710239f76c6`; make Python helpers
review mirrors only.

**Alternatives rejected:** narrowing the rule to canonical commands 1–4 would
silently alter executable semantics; changing command 7 to a different D4 map
would invent behavior; moving validation into Racket would not repair generator
API provenance.

**Probes:** rule smoke, grammar, Racket lint, authority sync, canonical pair
checks, and source-bound apply evidence.

**Failure modes and limits:** canonical visual demonstrations still do not prove
branches 5–8. Maintainer confirmation is appropriate if executable authority is
not intended to define training scope.

## D6 — quarter-turn direction as a separate episode parameter

**Candidate parameters considered:** command-2 quarter-turn direction, and a
more general per-command remapping. The latter was rejected because it would
create a large latent codebook, demand many more demonstrations, and cease to be
a small interpretable rule parameter.

**Decision:** prototype only `quarter_turn ∈ {clockwise,counterclockwise}`. Choose
once per episode, keep canonical clockwise as default, change only command 2,
and require an asymmetric command-2 demo and query.

**Probes:** real Racket execution for seeds 7300 and 7302; opposite-setting rival
checks; public/private separation tests; portable source-layout regression after
removing an accidental `scripts` namespace dependency.

**Failure modes and limits:** two settings and two seeds are existence evidence,
not a distribution study. Other commands do not identify the parameter. The
prototype is not wired into production, catalog approval, or the canonical rule.

## D7 — retain the current lesson rival set but bound the claim

**Decision:** use declared competitors (`ignore_command`, `always_cw`, and
`marker_only`) as finite diagnostics, plus the stronger canonical-only
commands-5..8 identity rival in the review answer. Report production and rotated
verdicts separately.

**Alternatives rejected:** calling zero named-rival survivors “unique rule
identification” would overclaim; ignoring hook warnings because rival ambiguity
is zero would hide the missing direct-command evidence; requiring arbitrary
rotations would reject the documented ordered curriculum without a downstream
need.

**Failure modes and limits:** undeclared rivals may survive. Exact input hashes
do not measure semantic diversity. Query rotation remains an explicit policy
boundary.
