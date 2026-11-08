# Review notes: `b9ada70e7181`

## Final decision

The base generator and one native parametric family are reviewer-ready on the
source bytes bound by `checks/b9ada70e7181/qualification-final/qualification.json`.
This does **not** grant owner approval, native acceptance, or training admission.

## Base defect and repair

The retained audit window at seed 222 contained demonstrations in which every
occupied column had only one pebble or a palindromic sequence. A reversed-stack
shortcut therefore matched the intended stable top-to-bottom packing rule. The
base sampler now constructively reserves a distinct-color, non-palindromic
same-column stack in every scene, keeps later placements out of that witness
column, and preserves exact requested dimensions across the documented 6..12 by
9..16 range. `self_check()` rejects scenes without the order witness.

## Parametric family

`gravity_policy=all_down` is the exact canonical Racket source. The alternative
`chamber_parity` performs a real two-stage computation: count all pebbles in each
wall-delimited chamber, derive even→up / odd→down, then stable-pack every column
against that input-derived edge. Inputs are identical across settings for a
matching seed. The family supports 2–6 demonstrations, exactly four distinct
queries, and a substantive 30×30 query.

## Findings during adversarial review

1. A first sampler version encoded direction by fixed chamber rank. Repaired by
   changing rank/direction relationships across the two-example minimum lesson.
2. Color and row-geometry summaries could substitute for chamber count on some
   seeds. Repaired with paired control chambers sharing width, row support,
   top/bottom rows, first color, exact color sum, unique colors, maximum color,
   and nonempty-column profile while having opposite count parity.
3. A count-threshold rule could fit some minimum lessons. Repaired by always
   crossing magnitudes: 6-up, 7-down, 8-up, and 9-down across the two demos, and
   by rejecting surviving count/color-sum monotone thresholds in `certify()`.
4. The certificate accepted duplicate inputs, Boolean grid cells, and forged
   one-demo lessons. Focused regressions now reject those cases, stale programs,
   tampered labels, too many demos, and a deliberately threshold-solvable lesson.
5. Certificate reporting initially claimed threshold checks for the canonical
   setting even though they were variant-only. The returned certificate now
   reports exactly the checks actually applied.

## Retained evidence and limits

The final focused suite has 21 passing tests. The final task-local adversarial
probe covers 128 seeds, 256 minimum-demo episodes, 1,536 scenes, all enumerated
rivals, 896 documented base-size draws, seven certificate attacks, and 36
protected-Racket evaluations. Authoring preflight covers four jobs and 32 more
protected-Racket evaluations. A protected witness changes the final output when
the parity-derived intermediate is inverted. The public projection exposes one
query per file; 24 first-turn private-field invariance checks and four positive
controls passed.

These finite seeds and explicitly enumerated rivals do not prove universal
uniqueness. The owner must still inspect the exact patch, rerun native
qualification and acceptance, and separately decide training admission.
