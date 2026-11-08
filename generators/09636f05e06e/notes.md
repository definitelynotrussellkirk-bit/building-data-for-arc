# 09636f05e06e — current decisions

## Canonical authority and current status

Generator version 2.0.0 supplies inputs for ARC `training:319f2597`. The rule
selects rows and columns containing **original input zeros**, clears their union,
and preserves color 2. Selection is simultaneous, not repeated from newly written
zeros. Canonical rule pin: `53141d69f404`. Generator SHA-256:
`0477dc50fdff9ac43529ebbddd8173ac0641eaf0311929f51d51439040493e69`.

This review (`review-dfd2ef16162b976a`) changes only task-local prototype, tests
and these notes. The canonical generator, rule ledger, base solution, frozen
fixtures and approval records retain their packet bytes. The supplied current
`evidence/review_index.json` lists decision `review-5d03dbd0f8e1d5fc:v0001` and
`audits: []`. Older appended notes saying its current audit was `needs_triage`
were stale; they are not a new open finding. This observation does not grant any
approval to the proposed parameter variants.

## Existing input contract and retained repair rationale

Exact dimensions are independently 8..22, actual zero-bearing row/column counts
1..5, and total palette size 3..10 including 0 and 2. Ordinary erased and protected
cells appear in both exclusive arms, an ordinary untouched cell remains, and an
ordinary cell beyond a protected cell distinguishes preservation from a barrier.
Palette representatives are planted last to avoid the retained last-color loss.
`twos_density` is a finite pre-witness Bernoulli probability 0..0.4, not an exact
realized proportion; zero still retains mandatory protected witnesses. Range
checking before float finiteness handles huge integers without OverflowError.

Textures are rectangle, scatter and single_zero; single_zero requires both support
counts one. Contradictory exact controls, unknown keys and invalid values fail.
Placement preferences are center, spread and edge. Difficulty changes default
weights, not the legality of explicit controls. Obsolete zero_density/position
aliases were intentionally removed in version 2; callers must migrate them.

The existing four-demonstration/one-query curriculum uses a seed-rotated cycle of
canonical, scatter, thin, scatter. Canonical profiles are 20x20, ten colors and a
2x2 zero block. Thin profiles vary support as 1x4 or 4x1; scatter exposes gaps.
Existing lesson checks use 13 declared rivals. Their historical finite coverage
does not establish all seeds, arbitrary override-built lessons or unlisted rules.
Mixed block-plus-isolated and other irregular connected supports remain omitted
from that default distribution. Strict validation describes a teaching subset;
canonical size/palette support is a separate profile question. Historical repair
and resolution assets remain under counterexamples/ without modification.

## Proposed two-parameter extension

`workspace/parametric/prototype.py` implements mode = both/rows/columns and a
protected nonzero color 1..9: 27 episode-fixed settings. Explicit `(both, 2)` is
the canonical reference setting, also the materialize_program default. Omitting
settings in build_episode/CLI selects them deterministically from the seed;
these seeded episode defaults are deliberately documented separately.

Every demo and query label executes the matching materialized Racket lambda.
The Python countermodel serves only as a hypothesis evaluator. Inputs come from
the unchanged generator, with settings-independent bounded rejection and no cell
editing. The prototype uses dimensions 12..22, all ten colors, support counts 2..4
and scatter/rectangle/thin profiles. All colors appear on both exclusive arms;
protected-then-ordinary rays and untouched cells provide useful contrasts.
This restricted authoring distribution is a proposal, not expanded production
support or proof about every canonical-domain input.

Teaching checks fit 27 settings and six structural forms per setting to demo
labels only. Survivors must agree on each query input before query labels are
executed. Equivalent forms can survive without causing ambiguity. The fresh-zero
rival initially approximated iteration as global erasure; a protected-barrier
witness disproved that. It now literally iterates the rule to a fixed point,
and a regression checks it against repeated Racket execution.

Counts are independently 1..32 demonstrations and 1..32 queries; default is 3/4.
The CLI accepts 1..16 seeds and each pair gets at most 256 input attempts.
Exhaustion, duplicate inputs and teaching disagreement fail explicitly. These
bounds do not guarantee success for every seed/count. Public bytes and IDs use
the shared projection helpers; private metadata and query answers are separate.
Batch IDs are sorted and duplicate visible payloads/existing destinations fail.
The writer does not promise crash-atomic publication.

## Evidence and next useful action

This return records 54 existing focused tests and 21 prototype tests passing.
An independent final-source check executes all 27 settings on seven shared inputs
(189 pair occurrences), checks 108 query predictions, and executes 108 additional
labels across four boundary grids. Reusing inputs deliberately isolates settings;
these are not 189 independent scenes. Two CLI episodes contain three demos and
four distinct queries each. The independent code review found no actionable
correctness defect in the final three new files.

Full production batteries, broad seed censuses and model learning were not run;
they are not required by this prototype-only change. No new variant approval or
training admission is claimed. The prototype README gives the runnable API/CLI.
The next useful work is an independently chosen lesson/seed evaluation against
additional concrete rival programs, followed by the maintainer's variant review.
Both separate supplementary tickets have bounded blocked outcomes documented
under checks/tickets/ in the return; they do not change this task's source status.
