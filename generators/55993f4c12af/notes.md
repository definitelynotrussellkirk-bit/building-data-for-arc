# Working notes: 55993f4c12af

## 2026-10-22 review `review-00947cea759dc138`

The current packet baseline was already semantically strong but failed strict
scalar validation: booleans, floats, strings, `None`, and negative sample indices
could reach generation. The repair validates `seed` as a literal integer and
`sample_index` as a nonnegative literal integer before `gen_ctx`. Valid draws,
version `3.0.0`, schedule, distribution, and canonical Racket authority are unchanged.

Final generator SHA-256 is `1024dbf16d342146ee85424d3c36d2514d6decfdaa192bba31d1759c495c6b48`. The official battery is 12/12 green,
portable task tests are 70/70, the production census is 0/300 ambiguous with
0/1,200 ambiguous query rotations, and the four-start cyclic probe is 0/300.
The focused regression was red for 13 invalid calls before the patch and green
after it.

A separate unapproved prototype under `workspace/parametric/` varies the episode
operator among canonical OR, XOR, and AND while preserving panel roles and ensuring
all four occupancy states in every demonstration. Racket-backed evidence covers
all three settings with 0 surviving parameter rivals and replays all five canonical
pairs under OR. The prototype is not selected production code.

Known limit: finite declared-rival checks do not prove universal induction. Audit
targets `548c1010ce89` and `5e3b849bd9c3` were findings-only and were not edited.

## 2026-10-04 review `review-43d4fa117b675f45`

Lead used: unverified prior audit `review-c3c6fa8c032ee1d2:v0002`, source SHA-256
`a4ac6959566b93f299e214db681bdcc66de9132d8e7b6fdff1b74b06ab2a0e92`.
It reported 121/1,500 sampled lessons where a top-half-only rival fit all three
demonstrations and failed the query. The current packet baseline independently
reproduced the underlying shared-support construction and four battery blockers.

The generator was rebuilt as version `3.0.0` around one invariant: every ordinary
input contains all four aligned occupancy states (`00`, `10`, `01`, `11`). The
public surface is now only five exact, observable controls. A four-slot schedule
keeps an exact canonical anchor at 25% while every three-demo sliding window also
contains an off-canonical example. The semantic contract declares executable
rivals, witnesses, canonical-fitting shortcuts, and `lesson_identifiable`.

Intermediate failures retained in `checks/` drove three corrections: paired
palette defaults looked like an alias, a five-slot anchor produced only 20%
canonical-profile support, and naive heavy counts on the 3x3 minimum could be
observationally balanced. Final source SHA-256 is
`f5bc92f43afad9f059e3e88e54a89e4bb12f5c246cd9d2729edaeae0933ed722`.
The final battery is 12/12 green, task tests are 52/52, the production census is
0/300 ambiguous, and the cyclic probe is 0/300 ambiguous.

The canonical Racket behavior was not changed. The bound base `raw_code` and
active `target_code` text were synchronized exactly to the canonical program,
with matching primitive-chain metadata, to remove authority drift.
## Current reviewer considerations

Source SHA-256: `1024dbf16d342146ee85424d3c36d2514d6decfdaa192bba31d1759c495c6b48`.

# Decisions for review `review-00947cea759dc138`

## D1 — Fix strict scalar validation at the generator boundary

**Measured defect.** The baseline `defect_lint` accepted values whose Python
coercions happen to work but which are not literal generation coordinates:
booleans, floats, strings, `None`, and negative `sample_index`. The source-bound
baseline finished 11/12 green, with 33 strict-scalar findings.

**Decision.** `_validate_call` now receives `seed` and `sample_index`; it requires
`type(seed) is int` and `type(sample_index) is int`, with `sample_index >= 0`.
The exact `type` check intentionally excludes booleans. The validation runs before
`gen_ctx`, so invalid calls fail consistently at the public boundary.

**Why not change `VERSION`.** The change only rejects calls outside the supported
contract. Bumping `VERSION` would change the RNG key and unnecessarily rematerialize
every lawful example. Valid generation remains byte-for-byte deterministic for the
same seed/index/overrides.

**Alternatives rejected.** Coercing with `int(...)` would silently accept values
that caused the defect. Letting `gen_ctx` reject them would keep the task-specific
boundary inconsistent and had already proved insufficient. Restricting seed to a
smaller arbitrary range was not justified by the current contract.

**Evidence.** `checks/scalar-red.log` failed 13/13 focused cases before the patch;
`checks/scalar-green.log` passed them after it. The final battery is 12/12 green
and portable task tests are 70/70.

## D2 — Keep the canonical distribution and authority unchanged

The selected generator already constructs all four occupancy relations in every
lawful input, provides a 25% exact canonical anchor, and has a four-slot schedule
that refutes its declared competitors. The only reproduced production defect in
this packet was argument validation. Therefore no distribution, label, rule text,
rule hash, schedule, or approval state was changed.

This is also the repair's shortcut self-review: because no lawful input/output
pair changed, the patch adds no visual regularity for a learner to exploit. The
canonical Racket rule remains hash `ce2dee847896` and source SHA-256
`4a881f6afe15a7d94c7976b3fa116e2f4a7c3831b163028bfdbc2284b63604ee`.

## D3 — Prototype one episode-level Boolean-operator parameter

**Parameter.** Select one operator per episode: OR, XOR, or AND over aligned
nonzero occupancy. OR is the canonical default. The parameter changes the rule,
not the input generator, palette, object roles, or panel alignment.

**Why this parameter.** It is the smallest rule-local variation that preserves
the original reasoning structure while producing meaningfully different labels.
Because each production input contains `00`, `10`, `01`, and `11`, demonstrations
can distinguish all three settings without adding artificial markers.

**Implementation boundary.** The prototype is under `workspace/parametric/` and
never replaces the selected canonical source. It materializes Racket by replacing
only the unique canonical Boolean condition, runs every label through the bundled
Racket bridge, writes separate public/private episode files, and records source
hashes. Seeds 1, 0 and 5 deterministically cover OR, XOR and AND.

**Alternatives rejected.** Output-color variation was rejected as cosmetic rather
than a rule-reasoning parameter. Swapping top and bottom panels is observationally
identical for commutative OR/XOR/AND. Varying panel count or geometry would alter
the task's object structure rather than provide a small original-family extension.
Mixing operators within an episode was rejected because it destroys a stable rule
for induction.

**Limits.** The three retained episodes establish bounded source-bound evidence,
not universal identifiability. The prototype is explicitly `proposed_unapproved`.

## D4 — Treat audits as findings-only

The drawn audit targets were not edited. For `548c1010ce89`, the fresh reproducer
confirmed a schedule-level columns-only shortcut on source SHA-256
`e006dcd911c368137baa9767168002b5283c172912f57597158bf4152ac0317c`.
For `5e3b849bd9c3`, a valid `n_rings=4` request on an 8×8 grid emitted one ring
and passed `self_check` on source SHA-256
`23ecd7d7379e129135baa59ef5f90b25f700ba4d62ae4ae142d0411b20515207`.
The suggested repairs are documented in `AUDIT.md`; neither source belongs to this
assignment's patch.

## D5 — Evidence and stopping rule

Failed and passing iterations are retained separately. Work stops after the final
source passes the official 12-stage battery, portable task tests, production and
cyclic lesson checks, parametric Racket evidence, both audits, and a fresh patch
replay. The exact source patch (`28bf9f3fff1e8beb512d78be3f8e7954ccd25c2b801baad7b685d6def969e9c6`)
was applied to a full untouched packet extraction; all six changed paths matched,
then 70/70 task tests and all 12 battery stages passed there. The first fresh-battery
transport was interrupted during `defect_lint`; the source-bound checkpoint was
resumed rather than discarded, and the final receipt records 0 interrupted stages.
Remaining uncertainty is stated as finite-evidence scope, not hidden as a claim of
universal induction.

## Current overlapping proposal

Unselected older-baseline alternative. Current accepted source 1024dbf1 already fixes literal seed/index validation while preserving version 3.0.0 and lawful seeded draws. It has 70 reported portable tests, a 12/12 battery and an unapproved source-bound OR/XOR/AND prototype. Proposed source 1d38b983 starts from f5bc92f4, overlaps generator/tests/notes/prototype and bumps version 3.0.1, changing the RNG namespace. Its 112 reported tests and 27 operation/color settings qualify only the proposed bytes. Retain the output-color extension for rebasing onto current source without replacing valid draws or current prototype. The reported complete 90,295-file fresh replay is retained as reviewer evidence; no owner execution, selected source/rule/prototype modification or variant approval. Retained at `workspace/proposals/review-89b132e69d909e18/manifest.json`.
