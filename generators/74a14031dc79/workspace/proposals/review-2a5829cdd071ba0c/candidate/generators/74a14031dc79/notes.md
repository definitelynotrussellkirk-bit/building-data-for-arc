# Working notes: 74a14031dc79

## Current rule and domain

The input is an `h×7` grid with a three-column left panel, a solid one-column
separator, and a three-column right panel. For each aligned panel position,
the output is blue (`2`) when either input cell is nonzero and black (`0`) only
when both are zero. The selected canonical Racket source is unchanged and is
pinned by `RULE_HASH = "582367af483f"`.

Lawful inputs use one distinct nonzero, non-blue color for each panel and the
separator; height is `3..12`. Canonical inputs are lawful even when they do not
show all four Boolean occupancy relations. Generated teaching examples are
stronger: every one contains `00`, left-only `10`, right-only `01`, and overlap
`11`, so left-copy, right-copy, XOR, AND, constant-fill, and input-blue shortcuts
are refuted within an individual example.

## Repaired distribution (version 3.0.0)

The imported 1.2.0 generator used one foreground color for both panels,
advertised density/pattern/target controls that were not recoverable, admitted
weak impostors through `self_check`, and never reached the canonical four-color
profile. Those choices were replaced rather than preserved:

- exact observable axes: `grid_h`, `left_color`, `right_color`, `sep_color`, and
  `relation_profile`;
- distinct panel/separator colors selected from `{1,3,4,5,6,7,8,9}`;
- five exact truth-table count profiles, each retaining all four relations;
- a four-slot schedule: slots 0 and 1 retain canonical height 3, slot 0 also
  anchors role colors `(6,8,4)`, and slots 2 and 3 use difficulty-banded heights;
- structural validation separated from the stronger generated-lesson profile;
- executable rivals, witnesses, canonical shortcuts, and a lesson-identifiability
  hook;
- unknown or incompatible exact overrides fail loudly.

Two height-3 slots are deliberate. A one-slot anchor produced only 10/60 hits in
the official pinned profile-floor census; the two-slot schedule produces 30/60
(11 easy, 8 medium, 11 hard) while every sliding three-example lesson still
contains off-canonical shape and palette evidence.

## Authority synchronization

`shared/data/base/solutions/training/e133d23d__74a14031dc79.json` had an
executable `target_code` using the legacy alias `cell-at`, while the canonical
selected source uses `at`. The task-specific `target_code` is now byte-for-byte
the canonical program. Archived `raw_code` remains unchanged. This is source
synchronization only; the canonical authority and behavior did not change.

## Evidence and limits

- Final generator SHA-256: `67d37e167fe4f56dc5b0c120a5a0466229ba98ffbae486432ac1a3d961c42c9d`.
- Final battery: 12/12 green at `checks/after-final/`.
- Portable task tests: 58/58 green at `checks/task-tests/`.
- Source-bound lesson census: 300/300 production lessons and 1200/1200 query
  rotations unambiguous against declared rivals, 1197 unique inputs, at
  `checks/lesson-census.json`.
- Strongest retained canonical shortcut and Racket-checked counterexample:
  `counterexamples/canonical-shape-palette-shortcut/`.

The finite rival set is not a proof of unique induction against every possible
program. The generator intentionally keeps the fixed 3+separator+3 geometry and
fixed output color 2 because those are task semantics, not nuisance features.
No unresolved selected-task blocker remains in this review.
## Current reviewer considerations

Source SHA-256: `11a12a0ad29bcf2ddc4bd744b1fc34ab0e1cf6fb30bf3ae9f966eaa8ca8078a3`.

# Decisions for review `review-92eccef38953659a`

## D1 — Preserve the selected distribution and canonical rule

The imported selected generator was already a mature `3.0.0` repair with exact
axes, full occupancy-truth-table teaching support, declared rivals, profile-floor
coverage, and retained shortcut evidence. The current review index points to
`review-c231a5768f77dff2:v0001`; I used that prior return only as a lead, then
remeasured the current source with the assigned battery and a new 300-lesson
census.

The before run found no distribution or rule defect before `defect_lint`; it
found a call-contract defect. I therefore did not rewrite sampling, palette,
shape, semantic rivals, or Racket authority. A broader rewrite would risk
regressing already-measured teaching support without addressing the reproduced
failure.

## D2 — Reject invalid call scalars at the generator boundary

**Choice.** Require `type(seed) is int`; require `type(sample_index) is int` and
`sample_index >= 0` before creating the generation context.

**Rationale.** Python accepts booleans as integers and downstream scheduling can
coerce floats/strings or let negative indices alias cycle positions. The before
`defect_lint` reproduced 33 warnings across bands. Rejecting at the public call
boundary makes invalidity explicit and keeps schedule semantics one-to-one.

**Alternatives rejected.** Coercing with `int(...)` would keep silent aliases;
validating only inside `schedule_profile` would leave other generation paths
exposed; broad seed range restrictions were not justified by the detector.

**Compatibility decision.** Keep `VERSION = 3.0.0`. Since valid outputs and RNG
choices are unchanged, a version bump would remap every lawful draw for no
semantic benefit. Final source hash is
`11a12a0ad29bcf2ddc4bd744b1fc34ab0e1cf6fb30bf3ae9f966eaa8ca8078a3`.

## D3 — Put new regression coverage in a separate reviewer test

The packet marks `tests/test_generator_74a14031dc79.py` as a frozen fixture. The
strict-scalar regression therefore lives in `tests/test_review_regressions.py`.
It checks Boolean, float, string, and negative cases with the selected module
loaded through portable `reviewer_support` paths. The inherited fixture was
restored byte-for-byte after the initial exploratory placement.

## D4 — Choose one meaningful parameter: the occupancy predicate

The family naturally supports one small rule parameter without changing object
roles: `occupancy_rule ∈ {or, xor, and}`. Each setting compares the same aligned
left/right panel cells, uses the same separator geometry, outputs the same
three-column shape, and paints with the same color 2. This preserves the original
reasoning structure better than changing panel width, colors, density, or height,
which would alter inputs but not the executed transformation.

The canonical/default `or` source is byte-identical to the pinned authority.
`xor` and `and` are generated by replacing one exact guarded condition in that
source; source guards reject whitespace or unrelated mutations. A target-color
parameter was rejected because color 2 is a visible task semantic and changing
it would create a mostly cosmetic variant. A direction parameter was rejected
because the task has no directional transformation.

## D5 — Select the hidden setting once per episode

`random.Random(seed).choice(("or", "xor", "and"))` chooses one rule for the
whole episode. All three demonstrations and the query use that exact Racket
source. Resampling per pair would turn the lesson into inconsistent supervision
and violate the packet's parametric contract.

Seeds 1, 0, and 5 were retained because together they exercise all settings.
This is bounded evidence, not a claim about seed frequencies.

## D6 — Require complete occupancy support in every prototype input

Every prototype input comes from the selected generator and contains all four
relations `00`, `10`, `01`, and `11`. That makes OR, XOR, and AND pairwise
distinguishable inside every demonstration, so query correctness never depends
on an unseen truth-table branch.

A weaker alternative—letting the three demonstrations collectively cover the
branches—could be valid, but it would require an episode resampling gate and
would create more ambiguous failures. The retained question counterexample at
`checks/question/finite-rival-ambiguity.json` shows why: OR and XOR both fit
three demonstrations lacking `11`, then disagree when the query introduces
`11`.

## D7 — Keep Racket as the only prototype label executor

The prototype materializes exact Racket for every setting and evaluates grids
through one persistent `RacketBridge`. A batch API was added after the initial
evidence-writer test exposed excessive one-grid subprocess round trips. Python
handles source guards, input construction, hashing, and rival bookkeeping but
never implements the output rule.

Public challenges are constructed by an allowlist: training inputs/outputs and
query inputs only. Seeds, selected parameters, Racket text, rule hashes, and
query outputs remain private. Evidence files are source-bound and hashed in
`checks/parametric/occupancy-rule-v1/manifest.json`.

## D8 — Do not integrate the prototype into production

The current runtime has no production parametric-rule API, and this packet does
not grant variant or training approval. The workspace is therefore separate
from `generator.py`; the selected `RULE_HASH`, canonical authority, catalog
status, and ordinary generation path remain fixed. Future integration requires
a separately reviewed API, admission policy, and broader seed/rival evidence.

## D9 — Recheck teaching quality on the final source

Although the scalar fix does not change lawful grids, I ran a current-source
census rather than relying only on prior notes. With three demonstrations per
query, `--per-band 100 --rotate-query` produced 300 lessons, 1,200 pairs, and
1,200 query rotations with zero declared-rival ambiguity and 1,197 unique inputs.
This verifies the actual final bytes against the declared rival set, not all
possible hypotheses.

## D10 — Keep audit targets findings-only

For `09647f283588`, I retained a source-bound reproducer showing the advertised
`overlapping_frames` texture destroys the first frame's shared corners and
leaves only one canonical-valid window. I did not edit that target.

For `a926d2195b22`, bounded inspection found no issue: 185 portable tests passed,
the task probe covered 128 override endpoints and 256 rotated lesson queries,
and 64 generated inputs matched canonical Racket output. This is a clean audit
within those checks, not universal approval.

## D11 — Close the pending external parametric-export correction

Review `review-2a5829cdd071ba0c` preserved the production generator and canonical
rule, then repaired only the proposed occupancy prototype. The retained external
manifest was explicitly `external_correction_pending`: its writer hard-coded
three demonstrations and one query, and public files were named by private batch
ordinal (`episode-NNN.json`). That made four-query evaluation impossible and let
seed/order metadata influence the public namespace even though it was absent from
the JSON body.

The v2 prototype exposes independent `demo_count` and `query_count` arguments,
defaulting to 3 and 4. It draws that many distinct selected-generator inputs with
bounded retries and rejects more than 16 total pairs. Public names now use
`reviewer_support.public_challenge_id` over the exact bytes returned by
`public_challenge_bytes`; the writer rejects duplicate visible payloads and the
writer sorts the batch by public identifier before assigning private episode
ordinals. The verifier replays counts, inputs, private episodes, exact public
bytes, identifiers, sorted report order, and every Racket label. Private
seed/setting/source and query-answer mutations keep the identifier fixed, while a
visible query-input mutation changes it.

Retained evidence at `checks/parametric/occupancy-rule-v2/` covers OR/XOR/AND
with seeds 1/0/5: 3 episodes, 9 demonstrations, 12 distinct queries, 21 replayed
Racket labels, 12 query-label replays, 3 opaque public identifiers, and zero
surviving declared parameter rivals. `checks/parametric/adversarial-v2/result.json`
retains the 16-pair maximum, 17-pair rejection, identifier privacy boundary, and
tampered-public-byte verifier rejection. This remains proposed/unapproved and
does not change rule hash `582367af483f`.

## D12 — Keep public focus `16de56c4` as a separate reasoning probe

The public demonstrations identify a progression rule: choose the orientation
with more same-color repeated-anchor groups; infer each group's arithmetic step
from gcd anchor gaps; extend the lattice to the grid edges unless one external
different-color point lies on it, in which case that point supplies the paint
color and terminal endpoint. Off-lattice distractors remain unchanged.

`workspace/public_focus_16de56c4/solver.py` is pinned to challenge SHA-256
`04f2c3b7aed8c16f787c41eb38d771d28bed8c54f4c649596974d8457a24edfd`,
replays all three public training pairs exactly, and retains predictions for the
two unlabeled public queries. Matching source `rule.rkt` (SHA-256
`dc53ff9b90a291d3e35f56ca4cda17e1dcc66810787e2db2a15480ef67635593`)
executes those demonstrations plus four distinct queries: the two public inputs
and two explicitly proposed support cases. All seven labels agree with the Python
probe. It rejects tied orientation evidence and ambiguous marker cases rather
than guessing. The progression/terminal-marker geometry has no honest structural
transfer into the selected two-panel occupancy comparison; forcing it into
production would replace object roles rather than parameterize them. Therefore
this remains a separate proposed extension, not lineage or training evidence;
the two public query predictions remain unverified, and the support-query labels
are claims only under the proposed rule.

## D13 — Supplementary tickets: one peer finding, one retained witness

For `258e1a721c75` (source SHA-256
`9cdc0d631cabeb95ff87a9c3bfecb77f8ca0dfcf82ef43abca7047243caa7e0a`),
one valid/invalid API comparison established a source-bound finding: baseline,
valid `palette_size=2`, and invalid `palette_size=999` were all accepted and
produced the same grid with a three-color palette. The advertised axis is not
consumed or validated. No peer source was edited; maintainer assessment is still
required.

For `66e63986855b` (source SHA-256
`8f78ef0944e40e80f9b86e9d5fdb2c9515fd05240e400d097e9993c5af79bc2f`),
the pinned seed at current default sample index 1 produced a lawful
`asymmetric_front` input. Canonical Racket rule `e9ecd02cbe2e` agreed with the
Python mirror and differed from the canonical-fitting `copy_upper_half` shortcut
on six cells. This is a completed bounded witness, not a universal peer audit.
