# Working notes: 7147e98f8173

## Baseline diagnosis

The baseline advertised variation but emitted one fixed scene: template, control
corner, marker positions, and effective displacement were constant. Most exact
overrides were absent or inert, the strongest canonical shortcut (one displacement
memorized per blue corner) was never challenged, `self_check` did not recover the
semantic axes, and the selected Racket record was semantically equivalent but not
byte-synchronized.

## Final design

Version 3.0.0 uses six exact, observable axes: canvas height 10..16, width
12..18, one of four corner controls, one of four asymmetric templates, and an
independent nonzero row/column vector in -4..4. Generation is constructive: it
chooses a legal red origin and marker origin so the rotated/translated output is
always in bounds; invalid scalar types, unknown overrides, and `(0, 0)` vectors
raise instead of being silently coerced.

A four-profile schedule deliberately repeats a corner with a new vector and a
vector with a new corner. Each exported lesson has seven demonstrations plus one
query. The generator declares executable rivals for corner-fixed displacement,
ignored rotation, ignored displacement, and identity, and `lesson_identifiable`
checks those declarations for every query holdout.

## Verification snapshot

Final generator SHA-256:
`6bd8c7d28389a00fa034c8a29fbb1f2c92bc0e2b0b93eb1d461b9af567e668ca`.
The after battery is 11/12 green; the only red stage is the shared semantic gate's
`declared_period_not_enumerated` warning. The required fixed-seed period census
then covered 12/12 lessons and 96/96 query rotations with zero ambiguity. A larger
300-lesson census covered 2,400 ordinary pairs and 2,400 query rotations with zero
ambiguity, hook warning, or scoring error. Task-local tests pass 10/10, including
the reusable `workspace/probe_contract.py`.

The selected Racket authority's executable semantics were not changed. Its
`target_code` text was synchronized exactly to `raw_code`, eliminating the
source-text drift found by `authority_sync`.

## Known record limitation

The frozen post-repair solve attempt contains a Python iterator-consumption bug
and genuinely executed as 0/7 visible examples. It is preserved unchanged.
`solve/corrected_solution.py` is a post-finish diagnostic only; the one-line
materialization fix replays 7/7 public examples without consulting private query
answers.
## Current reviewer considerations

Source SHA-256: `6bd8c7d28389a00fa034c8a29fbb1f2c92bc0e2b0b93eb1d461b9af567e668ca`.

# Decisions for review-07025d9ecc641a49

## D1 / R1 — Replace the fixed scene instead of patching lint metadata

The baseline's defects were behavioral: fixed geometry, dead axes, permissive
overrides, and no lesson-level rival contract. Merely adding `RULE_HASH` or
renaming axes would have made checks quieter while preserving the shortcut.
I replaced the sampler and retained the canonical rule unchanged.

Rejected alternative: keep random decorative textures around the fixed task.
Those textures do not alter the semantic relation and can increase superficial
diversity while leaving the absolute-coordinate solution intact.

## D2 / R1 — Six exact observable axes

I chose canvas height, canvas width, corner, template, row displacement, and
column displacement. Each can be recovered from the returned grid and is tested
at boundaries. Strict `type(value) is int` checks deliberately reject booleans,
floats, and numeric strings rather than coercing them.

The vector domain is -4..4 with only `(0,0)` incompatible. Four asymmetric
polyominoes are enough to exercise orientation without introducing symmetry
ambiguity. Larger shape libraries and longer vectors were deferred because they
would add placement/rejection complexity without addressing the diagnosed rule.

## D3 / R1 — Constructive placement

For a requested template, rotation, and vector, generation computes feasible red
origins and marker origins, then samples within those legal sets. This makes
exact overrides reliable and avoids an unbounded rejection loop. It also keeps
`self_check` and `observe_overrides` independent of hidden metadata.

Rejected alternative: draw arbitrary positions and retry. That obscures whether
an override is unsupported or merely unlucky and makes override enumeration
expensive and non-falsifiable.

## D4 / R1 — Four-profile curriculum, seven demonstrations

The schedule period is four:

1. canonical anchor;
2. same corner, new vector;
3. same vector, new corner;
4. independent corner/vector/template.

Seven demonstrations plus one query span almost two cycles, so each lesson
contains both kinds of decoupling regardless of query position. I tested every
query holdout, every period residue at seed 0 across three bands, and 300 random
lessons. An unordered random-only lesson policy was rejected because it would
not guarantee the needed witness in every exported lesson.

## D5 / R1 — Executable rival declarations

`corner_fixed_vector` is the strongest canonical shortcut because it fits all
four training pairs exactly. `ignore_rotation`, `ignore_vector`, and `identity`
cover the other direct component omissions. `lesson_identifiable` executes the
rivals against actual labelled pairs rather than trusting names or witness
frequency.

This is finite evidence against declared rivals only. I did not claim a proof
against all possible programs.

## D6 / R1 — Preserve canonical support in each band

Each band's schedule has a canonical-like anchor, and
`strict_canonical_like` recognizes only the five exact canonical axis profiles.
This keeps the profile floor measurable without making every generated sample a
near-copy of a canonical grid.

## D7 / R2 — Synchronize authority text without changing semantics

The selected authority had execution parity with canonical code but differed in
exact source text. I set `target_code` to the record's existing `raw_code`; the
Racket transformation itself was not redesigned. Authority sync and the
canonical Python mirror both pass afterward.

## D8 / R1 — Test-first repair and reusable probe

The initial task tests failed on missing constants/contracts and fixed behavior;
a focused red test for `workspace/probe_contract.py` then failed because the
tool did not exist. The minimal implementation made it green. Final task tests
are 10/10, and the probe emits a portable JSON report using only public reviewer
helpers.

The probe is intended for future agents: it materializes three bands, checks
axis recovery, labels with the Python mirror, rotates every query, and executes
the generator's actual declared rivals.

## D9 / S1 — Preserve the failed solve record

The post-repair solve hypothesis was correct but its standalone implementation
consumed an iterator twice. Because `finish` had already frozen the episode, I
did not rewrite the attempt or summary. I added a postmortem and diagnostic-only
corrected file, then replayed only the seven visible examples. This preserves the
training value of the real failure and avoids presenting a retroactive success.

## D10 — Compress only the oversized successful census

The 300-lesson census JSON exceeded the return's 25 MiB expanded budget by
itself. I losslessly gzip-compressed that successful report, recorded original
and compressed hashes/sizes, verified exact round-trip bytes, and retained a
small plain summary. All failure logs and reproductions remain directly readable.
