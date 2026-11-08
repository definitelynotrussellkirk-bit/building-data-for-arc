# Working notes: 44d20451ce17

## Current rule and authority

The selected rule is pinned by `RULE_HASH = "fc96c07b50d8"`. For every column,
erase every color-1 cell above the bottom row; if that input column contained at
least one 1, set its bottom cell to 1. Preserve every non-1 cell except a bottom
destination overwritten by 1. The canonical Racket behavior was not changed.
The selected `target_code` copy in the base solution was synchronized byte for
byte with the canonical program; archival `raw_code` remains intentionally
retained and is reported as archival-divergent by authority sync.

## Reversed baseline decisions

The imported v2.0.1 generator exposed many loosely coupled layout/density axes,
accepted invalid scalars and unknown controls, advertised a `no_ones` texture
that failed its own validator, and could accept `n_ones=6` while realizing only
four row cells or one diagonal/one-column cell. The prior audit
`review-daacac4ce0de0cac:v0001` (return ZIP SHA-256
`241f5e74939f1c2a8ff7f9c823c0da18c906943af9f91918f3b68bf5ed5152fb`)
was used as the lead for the retained underproduction reproducer; all baseline
claims were rechecked against pinned source SHA-256
`0d03aa6ad01f7d291f50d438ed37c1d0600865fb04afff37ad9432b84cdaa9ed`.

Version 3.0.0 replaces that surface with four exact observable controls:
`grid_h` and `grid_w` in 5..10, `n_ones` in 1..4, and `scene_profile` in
`canonical_scaffold|counterexample`. Seed, sample index, difficulty, scalar
controls, and unknown keys fail loudly when invalid. Every legal joint boundary
combination is constructive, and `self_check` recognizes only the two intended
profiles.

## Curriculum decision

Default samples alternate:

- `canonical_scaffold`: exact 5x5 canonical-style scenes, source row `h-3`, a
  gray 5 directly below each 1, and a gray bottom destination;
- `counterexample`: repeated 1s in one column from row 0, no direct gray support,
  and a black bottom destination while unrelated bottom cells remain gray.

Three demonstrations are exported. Every three-consecutive-sample window
contains at least one counterexample and refutes four executable rivals that all
fit every labeled canonical pair: bottom-5-only, direct-5-support-only,
fixed-source-row-only, and lowest-1-only. The retained exact witness is
`counterexamples/shortcut-counterexample-final.json`; the reusable checker is
`workspace/shortcut_probe.py`.

## Final evidence and limits

Final generator SHA-256 is
`ff9c89eb7fe655b851f32e1e273ad9065bab4f3fa8eb3d383bb973e2714869b0`.
The after battery is 12/12 green, task-local tests are 76/76 green, and a
100-lessons-per-band census materialized 300 lessons / 1,200 pair rotations with
zero ambiguity and 1,003 unique inputs. The exposed post-repair visible solve
passed 3/3 demonstrations on its first revision.

The generator intentionally covers only colors 0, 1, and 5; dimensions 5..10;
1..4 source ones; and two high-value visual profiles. The finite rival set and
census do not prove unique induction against arbitrary programs or all seeds.
Passing checks do not grant training approval; catalog approval remains external.
## Current reviewer considerations

Source SHA-256: `ff9c89eb7fe655b851f32e1e273ad9065bab4f3fa8eb3d383bb973e2714869b0`.

# Decisions for 44d20451ce17

## D1 — keep the canonical rule authoritative

**Decision.** Keep canonical Racket behavior unchanged and pin
`RULE_HASH = "fc96c07b50d8"`. Synchronize the selected base solution's
`target_code` text to the canonical program, but preserve archival `raw_code`.

**Rationale.** Rule-smoke evidence showed the task transformation itself was
sound; the generator contract and an active authority-copy mismatch were the
problems. Rewriting the rule would have changed the task rather than repaired
the generator. Authority-set SHA-256 after synchronization is
`f5e7e73fadfa450998bc5d2b44932b265b427b9e24161537da9918d5cba6f5b2`.

**Rejected alternative.** Treat the archival raw source as a second active
authority. It is intentionally historical and divergent, so using it would
reintroduce ambiguity rather than resolve it.

## D2 — replace the broad v2 surface instead of patching each layout

**Prior choice.** Version 2.0.1 exposed loosely coupled layout, density, and
texture controls. The original rationale is not documented and is therefore
unknown. Several controls were not independently observable or constructible,
and `no_ones` contradicted the task invariant and its own validator.

**New choice.** Version 3.0.0 exposes only:

- `grid_h`: integer 5..10;
- `grid_w`: integer 5..10;
- `n_ones`: integer 1..4;
- `scene_profile`: `canonical_scaffold` or `counterexample`.

**Rationale.** Each control now has exact pixel-level semantics and every legal
joint boundary combination can be constructed. This is simpler and stronger
than preserving nominal diversity that silently ignores requests.

**Rejected alternative.** Keep row/column/diagonal layouts and clamp requested
counts. Clamping would continue to lie about accepted overrides, and one-column
or short-diagonal layouts cannot realize all previously advertised counts.

## D3 — cap `n_ones` at 1..4

**Decision.** Use an exact finite range of 1..4 rather than a dynamic
`1..h*w/2` declaration.

**Rationale.** Four source cells are sufficient to expose same-column collapse,
while every value is constructible for both profiles at the minimum 5×5 shape.
The bound is probeable by generic tooling and makes exactness testable across
all dimensions and profile combinations.

**Failure mode avoided.** The retained baseline reproducer accepted a larger
request but realized fewer source cells. Version 3 tests the realized count for
every supported value and both profiles.

## D4 — use two purpose-built scene profiles

**`canonical_scaffold`.** A 5-supported visual grammar close to the canonical
examples: source row `h-3`, a gray 5 directly under each source 1, and a gray
bottom destination.

**`counterexample`.** Repeated 1s in one column, source cells beginning at row
0, no direct gray support, and a black bottom destination, while unrelated gray
cells remain available as distractors.

**Rationale.** The first profile preserves recognizability; the second supplies
one compact witness against several canonical-fitting shortcuts. Both are
recognized by a narrow `self_check`.

**Rejected alternatives.** `no_ones`, all-bottom-row, and singleton negative
textures were removed from the ordinary domain. An ordinary-gravity profile was
also rejected: the true rule collapses multiple same-column 1s to one bottom
marker, so preserving multiplicity would teach the wrong transformation.

## D5 — three demonstrations, then one query

**Decision.** Export three demonstrations and one query. Default samples
alternate profiles by sample index, so every three-consecutive-sample lesson
contains at least one counterexample. The query follows the demonstrations.

**Rationale.** Three examples are enough to retain canonical context while
forcing the semantic witness. Task-local tests enumerate every start residue of
the two-profile alternation and assert that each three-demo window refutes the
four declared rivals.

**Why no `LESSON_SCHEDULE_PERIOD`.** I removed an unsupported period declaration.
The routine semantic gate does not enumerate a declared period, and the larger
census is random rather than an exhaustive all-seed proof. The inexpensive
property actually needed here—every window of the two-profile alternation—is
covered directly by tests without overstating what the shared census proves.

## D6 — declare executable rivals and retain one exact witness

**Decision.** Declare the four strongest simple rivals that fit all labeled
canonical pairs:

1. move only when the bottom destination is gray (`bottom_five_only`);
2. move only when a 1 has a gray cell directly beneath it
   (`direct_five_support_only`);
3. move only from the canonical source row (`fixed_source_row_only`);
4. move only the lowest 1 in each column (`lowest_one_only`).

**Evidence.** `workspace/shortcut_probe.py` iterates the actual declaration,
checks all four labeled canonical pairs, and generates the retained seed-991,
sample-index-1 witness. `checks/shortcut-counterexample/racket.json` confirms
the intended output with the official Racket rule and matching hash.

**Limitation.** This is a finite, task-informed rival set. Passing it does not
prove that no other compact shortcut exists.

## D7 — strict validation and mutation-sensitive self-checking

**Decision.** Reject unknown keys and invalid seed/sample/difficulty/override
scalars rather than coercing them. Make `self_check` recognize only the two
intended grammars and expose `observe_overrides` for exact contract checks.

**Rationale.** Silent coercion makes generator recipes unreplayable, and a
permissive validator lets unrelated grids count as domain examples. Baseline
defect lint accepted five invalid `sample_index` values and found minimal
impostors; final defect lint is green.

## D8 — preserve failed and interrupted evidence

The initial before battery did not complete. Its source-bound summary remains
`running`: 2 green, lint failed, and 9 pending. Defect lint separately retained
one issue and nine warnings. During focused after verification, some Racket-
backed invocations stalled or produced incomplete evidence; each was retried or
resumed into a fresh/source-bound output rather than overwritten. The final
aggregate is 12/12 green. These attempts remain under `checks/` and are not
recast as successful first runs.

## D9 — post-repair solve and acceptance scope

The final visible-only solve was prepared from generator SHA-256
`ff9c89eb7fe655b851f32e1e273ad9065bab4f3fa8eb3d383bb973e2714869b0`.
Revision 1 passed all three visible examples without consulting a reference
during the solve. This supports human readability but does not expose or score
private query labels. Catalog approval and training admission remain external
decisions; this return requests routine acceptance of the repair, not automatic
training approval.

The final delta was also applied to a fresh extraction after verifying that Git
was rooted at that extraction's exact `WORK/` directory. All seven changed paths
matched the reviewed workspace, the generator SHA remained `ff9c89…`, and the
fresh task-test run passed 76/76. Evidence is under `checks/fresh-replay/`.

## 2026-10-23 parametric extension review

The selected v3 generator remains byte-identical at SHA-256
`ff9c89eb7fe655b851f32e1e273ad9065bab4f3fa8eb3d383bb973e2714869b0`;
the canonical rule remains `fc96c07b50d8`. This review added no production
API or authority change.

A proposed task-local family now lives under `workspace/parametric/`. Its one
parameter, `destination_edge`, is chosen once per episode with values `bottom`
(the exact canonical/default Racket program, SHA-256
`58a0c5aaca51aaa7a99d13233d936fa9406efa3a127bdc0dc4d88366a8d918c5`)
and `top` (SHA-256
`c06f627f1dc357b027559f73623a08ab97f6078340e453a5f5621db215b18938`).
Both preserve the column-presence and multiplicity-collapse reasoning. Each
retained three-demo episode distinguishes its opposite setting on all demos and
on the query. Labels are executed by Racket; public examples mask the hidden
setting, program, and query answers.

Current evidence: focused parametric tests 5/5, portable task tests 81/81,
after battery 12/12 green, and a fresh 100-lessons-per-band census with 300/300
materialized lessons, 1,200 checked rotations, zero ambiguity, and 1,003 unique
inputs. Evidence is under `checks/parametric/`, `checks/task-tests-final/`,
`checks/after-final/`, and `checks/lesson-census-current.json`.

Limits: the extension has only two rule values and two retained episode seeds;
finite opposite-setting and declared-rival checks are not a universal induction
proof. The prototype remains proposed and does not grant variant approval or
training admission.


## 2026-10-23 external prototype follow-up resolved

The public-export correction is now implemented without changing the selected
production generator (`ff9c89eb7fe655b851f32e1e273ad9065bab4f3fa8eb3d383bb973e2714869b0`)
or canonical rule (`fc96c07b50d8`). The task-local prototype source is
`7a767d4146a35d6e5a1d108be8aabd8a50a29bc04197e10966154fe6fd3cce6e`.

Each retained setting now has three demonstrations and four Racket-labelled
queries. For seeds 1 (`bottom`) and 0 (`top`), sample indices 0..6 produce seven
distinct lawful inputs per episode. The demonstrations distinguish the opposite
setting, and all four queries differ under that rival. All 14 labels match the
independent Python parity mirror. The exact canonical/default and proposed rule
hashes remain `58a0c5aaca51aaa7a99d13233d936fa9406efa3a127bdc0dc4d88366a8d918c5`
and `c06f627f1dc357b027559f73623a08ab97f6078340e453a5f5621db215b18938`.

Public challenge files are now named only by SHA-256 of their exact visible bytes and are
written in ID order after duplicate-payload rejection. The retained IDs are
`d792351784958cf67f5efb904b8ed7360d81f568b35614909c3336e10ea13dab` and
`f86c66a3ca44d4872b4853adc24d51e6285d6e1a956609ca33832e90f190fcd4`;
each file hash equals its ID. Hidden parameters, seeds, rule text, and query
answers do not enter those bytes. Because the compact return validator forbids
tracked-file deletion, the two legacy ordinal paths are retained only as identical
`arcpuzzles-retired-public-name-v1` markers with no challenge payload or setting
map; the writer rewrites them before every materialization. Evidence is
`checks/parametric/destination-edge-v2-evidence.json`; focused regressions are
7/7 green.

The earlier interrupted before battery and repetitive override-gate attempt
remain interrupted and are not recast as passes. They are unrelated to this
prototype-only export/count correction, so no production battery was rerun.
The extension remains proposed: two values and two retained seeds do not prove
all-seed teachability, approve a variant, or admit examples to training.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/44d20451ce17/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
