# Working notes: bc5e668b7668

## Review context

Assignment `review-88c10647a6e11300`, October 3, 2026. No prior review return was
used as a lead: `evidence/associated_notes.jsonl` was empty. The retained
`b90d4c3d5553` generator was consulted only as an example of the current
semantic/override contract shape, not as task evidence.

## Baseline findings

The selected `2.1.0` generator was not a sampled approximation of the official
task:

- it had no `RULE_HASH`;
- `self_check` rejected all five canonical inputs;
- defaults used palette cardinalities 3..9, while every canonical input uses
  all ten colors;
- defaults activated only 3..5 columns and prohibited row-0 values, while the
  canonical examples activate every column and sometimes contain row-0 values;
- six advertised axes were inert, partially honored, or silently ignored;
- unknown overrides were accepted;
- there was no executable semantic contract.

The before battery recorded 6 failed stages, 5 green stages, and 1 advisory in
`checks/before/checks/bc5e668b7668_before_battery_summary.json`.

## Canonical observations

The five official inputs have profiles `(6,6,10)`, `(7,5,10)`, `(6,7,10)`,
`(5,5,10)`, and `(6,6,10)`. Every column is active and contains two or three
nonzero values. Therefore the wrong rule “pack only columns with at least two
values; leave singleton columns where they are” reproduces all five official
outputs. This is the strongest retained task-local shortcut because canonical
cannot falsify it at all.

## Selected repair

Version `3.0.0` replaces the nine-axis synthetic sampler with three exact,
observable controls:

- `grid_h`: 5..9;
- `grid_w`: 5..9;
- `texture`: `canonical_dense`, `singleton_witness`, or `interleaved_order`.

Defaults stay on canonical profiles and use the complete `0..9` palette. The
four-slot schedule guarantees that any four consecutive demonstrations include
both a below-top singleton and an order witness. `self_check` accepts every
canonical input, enforces the selected grammar, rejects malformed/minimal
impostors, and no longer assumes values must begin below row 0. The semantic
contract declares two rivals and verifies their witnesses against the Racket
authority.

The first repaired defect-lint run found one additional real issue: difficulty
was inert. A regression test was added first, then easy and hard were assigned
disjoint subsets of canonical profiles. No Racket authority or canonical row
was changed.

## Verification summary

Final generator SHA-256:
`e1eccf31d384e706f3e98cb7fc7c67fbf3a4a43626db9938de7dfa26ce543455`.

- Focused task tests: 39 passed.
- Final after battery: 12/12 stages green.
- Lesson rival probe: 100 lessons per band, 500 inputs per band, 500 unique
  inputs per band; all four start residues occurred 25 times per band; both
  declared competitors were refuted by the four demos in every one of 300
  lessons.
- The `ignore_singletons` shortcut matched all 5/5 canonical pairs.
- Post-repair exposed solve: revision 1 passed 4/4 visible examples, with prior
  exposure declared `yes` and reference consultation declared `no`.

## Limits

The generator proves coverage only for its declared rivals, not every possible
wrong ARC rule. Overrides allow 5..9 dimensions, but default distribution is
intentionally narrower and canonical-scaled. Palette `0..9` is deliberately
fixed because that is invariant across every official input; this choice should
be revisited only if later task evidence establishes a broader lawful palette.
## Current reviewer considerations

Source SHA-256: `e1eccf31d384e706f3e98cb7fc7c67fbf3a4a43626db9938de7dfa26ce543455`.

# Decisions for `bc5e668b7668`

## D1 — Replace rather than patch the nine-axis sampler

The baseline advertised nine axes, but several were inert, partially applied,
or not recoverable from returned pixels. Its own `self_check` encoded a narrow
synthetic distribution that rejected all five official inputs. I replaced that
surface with three exact axes: `grid_h`, `grid_w`, and `texture`.

Rejected alternative: preserve every old axis and add special cases until the
battery passed. That would retain unsupported degrees of freedom, make override
provenance harder to audit, and leave future agents to reason about knobs that
do not correspond to task semantics.

## D2 — Keep defaults on literal canonical-scale profiles

All official inputs use one of `(5,5)`, `(6,6)`, `(6,7)`, or `(7,5)`, every
column is active, and each column contains two or three nonzero values. Defaults
therefore draw only those height/width pairs, then introduce a controlled
one-value column only in the semantic singleton branch. Explicit dimension
overrides remain available over 5..9 for bounded grammar generalization.

Rejected alternative: continue sampling arbitrary shapes by default. Shape
variation is not the rule's hard part, and broad default variation would spend
lesson capacity away from the canonical task while making profile-floor claims
less meaningful.

## D3 — Fix the palette to all ten colors

Every official input contains exactly colors `0..9`; the repaired generator
uses background `0` and ensures every foreground color `1..9` appears. This also
makes `texture` inference from pixels independent of hidden metadata.

Tradeoff: this is a real restriction. The generator does not claim that a
smaller palette is semantically invalid in the abstract; it claims only that
full palette is the validated distribution for this task. The restriction is
documented in `notes.md` and should be revisited only with new evidence.

## D4 — Teach the strongest canonical ambiguity deterministically

The wrong rule `ignore_singletons` packs columns only when they contain at least
two values and leaves singleton columns unchanged. It reproduces all 5/5
canonical input/output pairs because canonical contains no singleton column.
The `singleton_witness` branch forces a one-value column below row 0, making the
rules disagree visibly.

Rejected alternative: rely on a low-probability random singleton. Witness
frequency is not lesson coverage. A deterministic schedule gives a direct
lesson-level guarantee and a reproducible counterexample.

## D5 — Teach stable order, not just upward occupancy

A second rival, `sort_values`, moves every nonzero cell upward but numerically
sorts each column first. The `interleaved_order` branch inserts an `A-B-A`
sequence, which is nonmonotonic and must remain exactly `A-B-A` after packing.
The ordinary dense branch removes accidental `A-B-A` signatures so the texture
observer can recover the branch from pixels.

Rejected alternative: use only arbitrary dense columns and hope one is
nonmonotonic. That often refutes sorting, but it does not guarantee the intended
teaching distinction in every complete lesson.

## D6 — Use a four-slot schedule

The schedule is:

1. `canonical_dense`
2. `singleton_witness`
3. `interleaved_order`
4. `canonical_dense`

Any four consecutive samples contain both semantic witnesses regardless of the
start residue. The lesson probe uses five nonoverlapping examples per lesson
(four demos plus one query), so its starts cycle through all four residues.

Rejected alternative: a longer stochastic curriculum. It would require a much
larger census to establish complete-lesson witness coverage and could still
produce ambiguous local windows.

## D7 — Make every public control observable and fail loudly

Unknown axes, wrong types, booleans posing as integers, and values outside the
5..9/declared-texture domains raise immediately. `observe_overrides` recovers
all three exact axes from the returned grid. `self_check` validates the grammar;
`strict_canonical_like` separately enforces literal canonical profiles.

Rejected alternative: accept extra keys for forward compatibility. Silent
acceptance was one baseline defect and made override tests unable to distinguish
honored controls from ignored metadata.

## D8 — Make difficulty observable without inventing a new task

The first repaired defect-lint run correctly found that difficulty did nothing.
A failing regression test was added before the source change. Easy now draws
from `(5,5)`/`(6,6)`, hard from `(6,7)`/`(7,5)`, and medium from the overlapping
middle profiles. All remain literal canonical shapes.

Tradeoff: this is shape difficulty, not evidence that the mathematical rule is
intrinsically harder on those grids. It exists to make the public control
truthful while staying inside observed support.

## D9 — Keep labels and semantic verification authority-bound

The Python generator emits inputs only. `RULE_HASH` pins
`bd83e3df4565`; the Racket source and canonical rows were unchanged. The new
lesson probe invokes only the supported `arcpuzzles apply` path, checks both
executed rule hash and generator hash for every batch, then evaluates declared
Python rivals against those authority outputs.

Rejected alternative: use the local `_pack_up` helper as probe label authority.
That would test Python against itself and could miss a shared misconception.

## D10 — Build a reusable source-bound rival probe

`workspace/lesson_rival_probe.py` imports the selected module's actual
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES` instead of
copying names into the tool. It verifies canonical fit, all cyclic starts,
complete-demo witness coverage, competitor survival, input uniqueness, and
batch hash identity. Its plan construction has a focused regression test.

The probe intentionally does not enumerate every possible wrong ARC rule. Its
report states that limit, and the generator's declarations are the explicit
review surface future agents should extend when they identify another plausible
rival.

## D11 — Preserve failed iterations and audit boundaries

The red tests, the dead-difficulty intermediate failure, the first blind-solve
failure, and interrupted foreground driver logs remain in `checks/` or solve
attempt directories. Audit targets were analyzed using exact fixtures and the
supported authority path but were not modified; their findings are isolated in
`AUDIT.md`.

## Final self-review

The main new shortcut risk is distribution memorization: a solver could learn
that all valid defaults contain all ten colors and one of four shapes. Those are
validated task-distribution choices, not claimed rule preconditions; the actual
semantic schedule varies positions and per-column sequences while preserving
the intended transformation. The exact singleton witness in
`checks/question/finding.json` and the 300-lesson census demonstrate that the
repair closes the strongest observed semantic loopholes without changing the
reference rule.
