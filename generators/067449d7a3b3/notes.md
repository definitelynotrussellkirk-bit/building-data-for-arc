# Working notes: 067449d7a3b3

## 2026-10-24 native parametric family — reviewer ready

The retained audit showed a concrete teaching gap: ordinary examples could leave
4-connected and color-preserving 8-connected object parsing observationally
equivalent. The repair is a separate native four-setting family over two exact,
episode-fixed choices: `connectivity` in `{4, 8}` and `border_basis` in
`{min_side, max_side}`. The canonical default remains `{connectivity: 8,
border_basis: max_side}` and returns the selected Racket program byte-for-byte
(program SHA-256 `f30f6fac0820d39ec9e9e8598fe7bc08ce7f7e07015529eb0910f026844d9fd4`).
The production generator, canonical authority, and rule hash `fb156b8e3aee` were
not changed.

`workspace/parametric/prototype.py` now generates 2–6 demonstrations and exactly
four distinct queries with settings-independent inputs. Each demonstration
constructively separates both parameter axes and includes non-maroon, irregular,
and singleton objects to reject the finite named shortcuts. Queries cover
10×10, 16×18, 21×14 boundary/clipping, and substantive 30×30 stress scenes.
`visible_turn`, `visible_turn_bytes`, and `visible_turn_id` expose one selected
query only through the shared public projection, with no total-count hint,
future input, setting, program, seed, or answer. `audit.py` is a reusable finite
self-audit tool for future agents.

Focused tests pass 118/118. The finite audit covers seeds 0 and 17, demo counts 2
and 6, and all four settings: 16/16 lessons have one declared survivor, reject
all named shortcuts, use matched inputs, and never inspect query outputs. Native
qualification passed 8 jobs and 96 protected-Racket label executions; its four
program hashes are distinct. The source-bound inventory SHA-256 is
`886b46a4a4b911844fcd92c44d22d32562c0282baaf969f358be823bd7f43076`.

The required sequential dependency is object parsing and bounding-box/radius
measurement (A) followed by stem and clipped-halo coordinate selection (B). A
protected-Racket `wrong_intermediate` witness substitutes min-side radii into a
qualified max-side/4-connected case and changes the final 10×10 output. Evidence
is under `checks/067449d7a3b3/qualification/` and
`checks/067449d7a3b3/causal/`. This is reviewer-ready only: owner integration,
fresh exact-source qualification/acceptance, and any training admission remain
pending.


## Current bounded label-validation repair

The teaching hook previously accepted a supplied query output without comparing
it to the intended rule: with seed 91, indices 0..3, changing query cell (0,0)
still returned `[]`. It now rejects a supplied inconsistent query output with a
short reason, matching the existing demonstration-label validation. Input-only
queries remain supported. Sampling, version, default inputs and selected Racket
authority (`fb156b8e3aee`) are unchanged.
Audited source: `d22f31a2cbc127e7f38681daff9c421c45eb346af0441cb4a42bc3dcc7be2eca`;
repaired source: `a99b4745c87be0be95a1b46d3098123a962734c5f8552ee1d6560b9e33f28ee7`.

Focused evidence: `checks/067449d7a3b3/query-label-green.json` records four
Racket-backed pairs and every query rotation, including correct labels,
one-cell corruption and null labels; task-local tests pass 88/88. The initial
pytest invocation was unrun because dependency setup was still pending; the
direct regression invocation then failed as expected before the repair.
`workspace/probe_query_labels.py` reproduces the bounded check. The existing
unresolved four-connected shortcut teaching finding remains open; this repair
does not change its source-level support argument or claim to resolve it.

## 2026-10-07 repair

The baseline advertised negative fixtures as ordinary textures, silently
narrowed dimension overrides by difficulty, accepted unknown controls, provided
no executable semantic contract, and left selected solution text divergent from
the canonical authority. Canonical examples also permit three plausible wrong
rules: only maroon objects react, only solid rectangles react, and singleton
objects are ignored.

The repaired generator exposes four exact observable axes, accepts their full
Cartesian product in every band, and uses a `canonical, counterexample,
counterexample, canonical` schedule. Each counterexample simultaneously contains
a non-maroon L-shape and a maroon singleton, so any three demonstrations left by
a one-pair query rotation refute all declared rivals. The selected Racket rule
was not changed; both active selected `target_code` fields were synchronized
verbatim to the canonical `program_solution` while archival `raw_code` remained
untouched.

## 2026-10-07 final curriculum uniqueness pass

The first source-bound curriculum probe exposed two different byte-level duplicate
risks that the standard lesson census did not reliably cover. Adjacent X slots
could select the same counterexample placement, and seed `20261007` produced an
identical canonical pair across the schedule's C|C boundary at sample indices
27 and 28. A runner that filters duplicate pairs can silently replace a required
counterexample or change the three-demo teaching set even when every individual
pair is correctly labelled.

Version 4.0.2 makes both adjacent slot classes structurally distinct: the two X
slots use opposite deterministic placement preferences, and the first canonical
rectangle uses a different modulo-four corner anchor in every schedule slot. The
reusable `workspace/probe_curriculum.py` now enumerates cyclic four-pair windows,
checks pair digests before runner de-duplication, and evaluates every possible
query rotation. Its final run covered 288 windows, 1,152 materialized pairs, and
1,152 rotations with zero duplicates or rival ambiguity.
## Current reviewer considerations

Source SHA-256: `d22f31a2cbc127e7f38681daff9c421c45eb346af0441cb4a42bc3dcc7be2eca`.

# Decisions for `067449d7a3b3`

## D1. Preserve the selected transformation law

**Decision.** Keep rule hash `fb156b8e3aee` and the canonical Racket
`program_solution` unchanged.

**Rationale.** The canonical examples, original generator intent, and selected
Racket implementation all describe the same object-bounding-box halo/stem law.
The observed failures were generator-contract, curriculum, and authority-text
problems, not evidence that the canonical transformation itself was wrong.

**Alternatives rejected.** Rewriting the Racket rule would have enlarged scope,
invalidated canonical authority binding, and obscured whether generator repairs
were correct. Keeping divergent active `target_code` text was also rejected:
identical intent is insufficient when the review tooling binds exact source.

**Probe and failure mode.** The authority stage executes each source on all
canonical pairs. The final selected set is one exact group; archival `raw_code`
remains separate but executable. Limitation: canonical-pair parity does not prove
arbitrary-input equivalence between archival and canonical implementations.

## D2. Replace misleading textures with four exact observable controls

**Decision.** Advertise only `grid_h`, `grid_w`, `n_objects`, and
`scene_profile`, with full Cartesian support in every difficulty band.

**Rationale.** A declared control should be recoverable from returned pixels and
honored exactly. Grid dimensions, object count, and the two semantic profiles
meet that standard. Difficulty now selects defaults only; it cannot silently
narrow an explicitly requested value.

**Alternatives rejected.** The baseline `no_rects` and `full_grid` textures were
negative fixtures outside the intended production domain. Retaining them as
ordinary profiles would force `self_check` either to accept invalid task inputs
or to reject advertised generation. Silent clamping was rejected because it
makes provenance and multi-axis tests meaningless.

**Probe and failure mode.** Contract tests cover boundaries, types, all bands,
and combined overrides; the shared override audit made 3,780 draws with zero
findings. Limitation: exactness is guaranteed only for the documented axes.

## D3. Use canonical anchors at task-relevant sizes

**Decision.** Canonical defaults use maroon solid rectangles at 10×10, 20×20,
and 30×30 anchors for easy, medium, and hard, with 15×15 for the default band.
Object count remains independently controllable from 2 through 4.

**Rationale.** These anchors preserve the original canonical palette and shape
family while spanning the supported envelope and guaranteeing an exact profile
hit in every band. Hard canonical generation includes a 6×6 object, matching the
largest canonical object scale exercised by the rule.

**Alternatives rejected.** Purely random sizes made profile-floor support
probabilistic. Restricting all examples to the exact canonical grids would have
reduced diversity and left no room for exact dimension controls.

**Probe and failure mode.** The profile-floor stage accepted all 10 canonical
inputs and found exact support in all bands. Limitation: the chosen anchors are a
generation curriculum, not a claim that only those dimensions are lawful.

## D4. Put all three shortcut-killing features into each counterexample

**Decision.** Every counterexample profile contains a non-maroon irregular L
object and a maroon singleton.

**Rationale.** The L simultaneously refutes `maroon_only` and
`solid_rectangles_only`; the singleton refutes `ignore_singletons`. Co-locating
features means one counterexample demonstration is sufficient, making every
three-demo query rotation teachable under the four-pair schedule.

**Alternatives rejected.** Separate one-feature counterexamples would require a
larger minimum demonstration count or a more fragile schedule. Randomly choosing
which feature to include could leave a lesson compatible with one rival.

**Probe and failure mode.** The semantic gate observed both witnesses in
281/600 draws and verified 60/60 Racket-backed rival disagreements per witness
claim. Limitation: the witnesses target the declared rivals, not all conceivable
shortcut rules.

## D5. Use an explicit `C-X-X-C` schedule with three demonstrations

**Decision.** Materialize four pairs in the repeating order canonical,
counterexample, counterexample, canonical; hold out one pair as query and expose
the remaining three as demonstrations.

**Rationale.** Every cyclic four-pair window has two canonical anchors and two
counterexamples. Removing any one pair leaves at least one counterexample, so all
three declared rivals are refuted by the demonstrations regardless of query
position. Three demos retain the packet's intended compact lesson format.

**Alternatives rejected.** Independent Bernoulli profile sampling permits
all-canonical lessons. A single fixed counterexample position works only when the
query position is fixed. Four demonstrations would work but is unnecessary once
the schedule is rotation-safe.

**Probe and failure mode.** The required semantic gate checked 48 rotations; the
large census checked 1,200; the task-local cyclic probe checked 1,152. All were
identifiable. Limitation: downstream code must preserve the four-pair assembly
semantics or perform an equivalent check after transformation.

## D6. Make adjacent scheduled pairs structurally distinct

**Decision.** Give adjacent X slots opposite deterministic placement preferences,
and give the first canonical rectangle a distinct modulo-four corner anchor.

**Rationale.** Lesson runners may reject duplicate labelled pairs and advance to
a later sample index. A semantically correct but byte-identical pair can therefore
change the intended profile sequence. Structural distinctions are stronger than
hoping color or RNG variation happens to differ.

**Alternatives rejected.** The first repair relied on random placement/color and
failed for adjacent X slots. After fixing X, canonical random placement still
failed for seed `20261007` at the `C|C` boundary (indices 27 and 28), retained in
`checks/curriculum-probe.json`. Merely increasing retry limits would hide rather
than fix the contract drift.

**Probe and failure mode.** `workspace/probe_curriculum.py` hashes complete
input/output pairs before any de-duplication and checks all query rotations.
The final run found zero duplicates in 288 cyclic windows. Limitation: the probe
covers the declared seeds/start range; structural construction, not that finite
sample alone, is the primary guarantee.

## D7. Keep canonical and counterexample profiles easy to observe

**Decision.** Canonical grids contain only solid maroon rectangles; counterexample
grids contain both the non-maroon irregular object and maroon singleton.
`observe_overrides` classifies from those pixel properties.

**Rationale.** Observable profiles let override tests validate actual outputs and
let future agents diagnose a lesson without private RNG state. The distinction is
semantic and tied to shortcut coverage.

**Alternatives rejected.** Hidden profile metadata or bookkeeping-only checks
would repeat the baseline provenance failure. Allowing arbitrary non-maroon
rectangles as a third implicit profile would make validation ambiguous.

**Probe and failure mode.** Tests mutate generated grids into one-rectangle and
arbitrary non-maroon-rectangle impostors and require `self_check` to reject them.
Limitation: profile classification is intentionally narrow rather than a general
object taxonomy.

## D8. Add source-bound tests and a standalone reusable probe

**Decision.** Add `tests/test_generator_contract.py` and
`workspace/probe_curriculum.py`.

**Rationale.** The shared battery catches broad contract failures, while the task
needs regression coverage for exact axes, malformed inputs, canonical parity,
executable rivals, active authority text, cyclic schedule windows, and duplicate
pair behavior. The probe is standalone so future reviewers can use it without a
preconfigured `PYTHONPATH`.

**Alternatives rejected.** Relying only on the standard 12-lesson semantic smoke
missed the duplicate-window problem. The 300-lesson production census also did
not enumerate every cyclic start used by the task-local schedule.

**Probe and failure mode.** The portable task snapshot reports 87 passing tests;
the standalone probe test removes `PYTHONPATH` and executes from a temporary
working directory. Limitation: tests bind the intended current interface and
must be updated deliberately if the production lesson assembler changes.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/067449d7a3b3/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
