# Current decisions: 48283e01e8ab v3.1.0

## Intended rule and authority

Find orthogonally connected components of color 6. Sizes 6, 5, 4 and 2 become
colors 5, 3, 8 and 9. A three-cell horizontal/vertical line becomes 2; another
connected three-cell shape becomes 4. Other sizes remain 6. Preserve every
non-6 cell and the grid dimensions. Background 7 and the output color table
are fixed semantic symbols, not interchangeable palette parameters.

The canonical Racket text and canonical ledger are unchanged; `RULE_HASH`
remains `79a3d3708716`. The two selected base `target_code` fields were
synchronized to the exact canonical whitespace after a failing authority-sync
check. Their archival `raw_code` fields remain untouched. This was not a rule
change. Imported associated notes retain earlier evidence in
`evidence/associated_notes.jsonl`; this file records the current decisions.

## Teaching repair

The old independent profile sampler admitted a concrete teaching failure:
seed 61, medium, indices 0–3 gives three demonstrations that fit a canonical
shape-template classifier, followed by a query whose T-shaped four-cell
component refutes it. The retained complete lesson and Racket labels are in
`counterexamples/baseline_seed61.json`. The final task-local authoring probe
`workspace/shortcut_probe.py` re-executes that lesson and a repaired lesson.

The old `all_classes_once` scene covered the six recognized shape classes.
It now covers every emitted size class, including unchanged sizes 1, 7 and 8,
preserved foreign cells, and noncanonical shapes at sizes 4, 5 and 6. All 16
original profile names remain available; the other 15 keep their prior shape
families and the three exact public masks are unchanged. The old six-class
input signature remains accepted, so this enrichment does not reject that
existing input family. Rich scenes use 12×12, 13×13 and 14×14 grids by band.

Default unforced roles repeat `teaching_core, general, teaching_core, public`.
`teaching_core` generates the enriched `all_classes_once` profile; the role name
is not an extra override value. `EXAMPLES_NEEDED = 4` requests four demonstrations.
Any five consecutive default draws contain at least two rich scenes. Holding
out any one pair leaves a complete teaching scene for every emitted size class
and all seven declared rivals. General slots retain all 13 general profiles;
public slots select among the original three public inputs. Exact forced
profiles remain authoring controls and do not inherit this lesson guarantee.

Six declared canonical-fitting rivals have explicit generated witnesses. The
seventh rival, treating every three-cell component as straight, is already
refuted by canonical examples but is retained as a lesson check. The hook checks
demonstrated class labels, foreign-cell preservation support, and declared-rival
consistency. This is a bounded teaching contract, not unique inference among
all possible rules.

Strict draw validation rejects booleans, floats, strings and negative identities;
seed and sample_index must be nonnegative Python integers. Difficulty is
validated even for an exact public profile. Unknown controls are rejected.
All actual profile choices use the public keyed-draw provenance API. The
validator rejects malformed colors, ragged or oversized grids without claiming
to accept every grid on which the Racket transformation is mathematically defined.

## Current evidence and limits

Review `review-89effc2f42a416a4` retains a complete final 12-stage battery,
48 passing task cases, a Racket-labeled 300-lesson / 1,500-holdout census,
and all four cyclic starts at seed 0 in all three bands (12 lessons / 60
holdouts). Full source identities, exact commands, failed iterations and
fresh-replay status are in that return's `RESULTS.json` and `checks/`.

Rich teaching scenes are larger than ordinary scenes, making their role
detectable from dimensions; the finite shape bank remains memorizable. The
repair closes the named counterexamples but does not demonstrate broad
shape generalization. Unknown emitted sizes are only 1, 7 and 8; larger sizes
are not part of this generator's stated sampling support. Random placement
has a bounded retry budget, not a proof of success for every possible seed.
The production runner can skip rejected or duplicate draws; the structural
argument concerns consecutive windows, while retained censuses measure the
actual accepted lesson populations and their retry behavior.
Do not shorten demonstrations, force one profile for an entire lesson, or
arbitrarily subsample pairs and reuse the default guarantee without checking
the resulting lesson. Multiple-query solve execution is recorded separately;
the exhaustive holdout result concerns one query at a time.

## Proposed rule extension

`workspace/parametric/connectivity.py` is an unapproved prototype with one
episode-fixed parameter in `{4, 8}`. Setting 4 returns the exact canonical
program text; setting 8 adds only diagonal neighbors. Both settings are
Racket-executed, and every proposed episode has three demonstrations plus one
query that distinguish the parameter. The six contact templates are a narrow
contrastive sampler. This proposal does not change the selected rule, catalog
registration, or training approval. See its README and the retained parameter
evidence for the separate 24-episode / 96-holdout measurements.
## Current reviewer considerations

Source SHA-256: `7e39b033ea4ac165e40c8b2e97663b1c41f9a4203254957b8ef470c191108927`.

# Decisions — review-89effc2f42a416a4

## Scope and authority

The assignment is the supplied original ARC family `training:ad38a9d0`, selected
task `48283e01e8ab`. Parametric design began in parallel with the initial
canonical diagnosis, and the standalone prototype was completed before final
canonical verification. The blind solve was finished before either activity.
Audit IDs were drawn once and neither audited generator was edited.

The transformation is component detection → size/shape classification →
in-place recoloring. This is one reasoning pattern with dependent stages,
not independent rules concatenated merely to make an example look complex.
The canonical record supports three unique input/output pairs appearing in
six usable labeled occurrences across two rows. Tests and counts retain both
denominators instead of treating duplicated occurrences as independent puzzles.

The earlier notes were a placeholder, and the full historical rationale for
every old shape family is unknown. Where a name or source structure suggests
an intention below, that is an interpretation, not a claim about its author.

## Distribution choices

| Choice | Earlier behavior and failure mode | Final decision and rationale | Evidence / limit |
|---|---|---|---|
| Exact public support | Three fixed original 9×9 inputs among 16 independently selected profiles | Preserve all three exact masks; give a public role one slot per four default draws | Final profile floor: 20/60 exact/envelope hits; public slots intentionally contain only three unique grids |
| Background and source colors | Background 7; source 6; all other colors preserved | Keep these symbols and the full output table fixed | Canonical Racket authority; blanket palette permutations would change fixed semantics |
| Known size classes | `all_classes_once` used rectangle6/plus5/skew4/line3/bend3/domino | Enrich it with zigzag6/L5/T4 plus both threes/domino, unknown sizes 1/7/8 and foreign cells | Closes canonical-template memorization and supplies every emitted class; old six-class inputs still accepted |
| Profile interface | 16 named exact scene controls | Keep those 16 names; no additional 17th control | An intermediate extra profile exceeded the shared finite-enum cap; consolidation also avoids a redundant public axis value |
| Other scene families | Repeated lines/bends, unknown sizes, noncanonical shapes, dominoes, edges, foreign cells and mixed repeats | Preserve their shape banks and forced behavior | Existing exhaustive forced-profile tests and 1,530-draw override check; not all possible polyominoes are sampled |
| Placement | Random dihedral orientation and position, no orthogonal contact between intended objects | Keep local seeded randomness and the placement rules | Deterministic repeat/RNG isolation tests; diagonal contacts remain possible; bounded retry budget is not a totality proof |
| Rich scene dimensions | Ordinary general grids were easy9×9, medium9×10, hard10×10 | Rich scenes use easy12×12, medium13×13, hard14×14 for reliable nine-component placement | This changes a distribution axis and reveals scene role from dimensions; disclosed rather than called broad generalization |
| Unknown sizes | Separate profile included1/7/8 and a domino | Teach all three in every rich scene so a held-out unknown-size query has direct support | Sizes≥9 are outside emitted support; preserving every other size is the rule, not a sampled-coverage claim |
| Foreign colors | Five preserved cells in one family | Add five to each rich scene, using three distinct non6/non7 colors | Enough to refute erasing foreign cells; their spatial patterns remain constrained |
| Draw identity | Public profiles bypassed validation; scalar coercions accepted | Require nonnegative Python integer seed/index, validate band first, reject unknown axes | 20 review regressions; final defect lint green; this narrows accepted argument types deliberately |
| Provenance | First scheduled draft chose internal subprofiles without recording exact axis `scene_profile` | Route the scheduled final choice through `draw_choice('scene_profile', [chosen])` | Records real public keyed-draw provenance, no fabricated metadata; final override warnings 0 |

## Lesson assembly and evidence

The old independent sampler could supply three narrow demonstrations and a query
that introduced a previously undistinguished size/shape rule. At seed 61 medium,
indices 0/1/2 contain only repeated bends, repeated lines and dominoes, while
index 3 includes a T-shaped four-cell component. A classifier restricted to the
six original dihedral shape templates fits the demonstrations and all six
canonical occurrences but leaves that T unchanged. The original selected
Racket execution and the final re-execution both confirm the wrong query.

The final default is an explicit four-slot role schedule:
`teaching_core, general, teaching_core, public`. Layouts and subprofile choices
are still seeded. `EXAMPLES_NEEDED = 4` lets the supported automatic lesson
builder use four demonstrations. The general role selects from all 13 general
profiles, including the richer all-class scene; the public role selects from
the three exact public inputs. The core role always chooses the enriched
`all_classes_once` input family.

Any five consecutive indices contain at least two core roles. With one pair
held out, at least one core remains among the demonstrations. That remaining
pair includes every class emitted elsewhere—1, 2, straight3, bent3, 4, 5, 6, 7
and 8—plus foreign-color preservation, and refutes each of the seven declared
rivals. This is a structural argument for the declared contract when all draws
materialize. It does not make arbitrary rules uniquely inferable and does not
prove that bounded placement succeeds for every possible seed. The production
runner can skip rejected or duplicate draws; arbitrary such skips are outside
the consecutive-window argument. This is why the actual materialized-lesson
censuses are retained in addition to the structural argument.

The final production census independently executes reference labels for
100 lessons in each of easy/medium/hard. Seed generation is the shared
SHA-based recipe and requested start indices are 0–99; materialized indices are
retained. It reports 300 lessons, 1500 pair occurrences, 1158 unique inputs,
zero production ambiguities and zero ambiguities in 1500 holdouts. Its generic
diagnostic modulus 6 is not the generator period. A separate fixed-seed 0 run
enumerates all four actual period residues across the three bands: 12 lessons,
60 pair positions/holdouts, 20 unique inputs, all passing. These populations
overlap and are not added together as independent training examples.

The hook learns output labels from demonstrations by component class and checks
foreign-cell demonstration support. It also evaluates every declared lesson
rival against demonstrations and query. Six rivals fit all usable canonical
pairs; `all_threes_are_lines` does not, and is labeled only as a lesson rival.
Every canonical-fitting rival has an explicit witness link. Racket supplies
the retained labels; the Python mirror is cross-checked but not treated as
independent authority. `workspace/shortcut_probe.py` iterates declarations
directly and demonstrates the old failure and repaired same-seed window.

## Alternatives considered

Increasing only the frequency of noncanonical shapes was rejected: a witness
can be common across a dataset yet absent from a particular lesson. Keeping
three demonstrations with only one complete teaching example was rejected
because a query rotation could remove that sole example. Merely adding more
rivals without changing lesson assembly would detect the same teaching defect
without repairing it. Changing the canonical Racket program to recognize only
original shape templates was rejected because it would encode the shortcut
and contradict the intended size rule.

The first repair introduced a new `teaching_core` override value, producing
17 scene values. The included checker caps finite enum probing at16. Marking
that finite domain diagnostic or silently dropping a legacy scene would evade
the contract or narrow it without justification, so both were rejected. The
final design enriches the existing all-class concept and preserves the other
15 control values. The intermediate source and failed lint/override/semantic
receipts remain in the return. Exposing an adjustable shared probe budget is
separate tooling feedback, not an applied shared-source change.

A second public control to toggle teaching completeness was rejected as
unnecessary API complexity. Reducing rich scene sizes to match canonical9×9
would tighten placement substantially; this return instead takes the explicit
larger-grid tradeoff. A future broader sampler should reduce the size cue and
expand connected shape support, with new counterexamples and rerun lesson
checks. No claim about that unbuilt distribution is made here.

## Canonical authority and test migration

The before battery found only an exact-text authority divergence: two selected
base `target_code` strings were minified while the canonical rule was formatted.
Execution parity already passed. The supported `authority-sync --selected-only`
proposal was inspected and applied to those two assigned paths. Canonical
ledger bytes and archival `raw_code` bytes are unchanged. Canonical exact rule
SHA is `39bd0e54016ec5a34e379f252fdf559246c4b88548bc9d94b7937666916f7148`;
the normalized pin remains `79a3d3708716`. All final authority checks pass.

Before task tests failed because an editable selected test used a fixed parent
path and a private per-puzzle import. It now uses `find_root`, `canonical_path`,
`canonical_pairs` and `load_selected_generator`. Original oracle comparisons,
all 6 canonical occurrences, and the broad forced-profile/diversity tests remain.
No frozen root fixture was edited. Red test evidence and final 48-case results
are retained rather than turning the initial collection error into a pass.

## Parametric assessment — proposed, unapproved

Connectivity in `{4,8}` is one small structural parameter: it changes whether
diagonally touching source cells belong to one object while preserving object
roles, the size calculation, three-cell straightness, fixed output colors and
in-place recoloring. The value is drawn once per episode and never independently
per example. It does not affect the input sampler, so layout or palette does
not encode which setting was chosen.

The default materializer returns the exact canonical Racket text. The alternative
adds only four diagonal BFS neighbors, yielding normalized rule hash
`d9abd9d2deb1` and exact SHA
`024721e3ba6cf9cb13e2951ea851ce3642b01e4a4f65e5231ed9238a97ba3352`.
Both rules execute through the public Racket bridge. The sampler uses six
diagonal-contact templates that pass the canonical input validator. Each
episode has three demonstrations and one query; every pair separates the two
parameter values, so every one-pair holdout remains informative.

Final evidence on the final canonical generator checks seeds 0/1/17/83,
three bands and both settings: 24 episodes, 96 pair occurrences, 45 unique
inputs, 24/24 production and 96/96 holdout identification. Default canonical
agreement is 6/6 occurrences representing 3 unique pairs; 6/6 witness profiles
separate the settings. There are 18 focused prototype test cases. Public JSONL
contains only visible demonstrations and query inputs; parameter values,
source identities and query labels are in a separate private export.

Alternatives such as arbitrary output-color remapping would add a larger
lookup-table learning burden and change the original color semantics. More
than one new parameter was unnecessary to demonstrate a meaningful extension.
The prototype's contact-heavy finite templates are deliberately narrow; only
the two declared connectivity rivals are distinguished. It is not registered
as a canonical variant, not approved, and not evidence of arbitrary shape-rule
identifiability or improved model performance.

## Solves, audits and retained uncertainty

Both solve records contain one genuine revision and 4/4 visible-example passes.
The first solve is blind; the main post-repair solve is exposed and explicitly
reports prior authoring knowledge. No reference was consulted during either
solve. Masked-query correctness remains unknown, and no intentional wrong
solution is presented as a naturally failed attempt.

The two audit findings remain separate from the canonical repair. The color-
frequency rival is an accepted-domain curriculum gap, not an observed wrong
generated label. The ignored-control defect concerns requested input controls,
not reference correctness. A canonical-input validator mismatch in the second
audit is explicitly a domain question. No audited source or inherited approval
status was changed.
