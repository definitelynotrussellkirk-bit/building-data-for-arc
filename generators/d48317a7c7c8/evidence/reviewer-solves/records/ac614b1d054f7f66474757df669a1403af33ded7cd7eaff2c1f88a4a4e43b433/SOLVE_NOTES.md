# Post-repair solve work log

## Exposure

This is an exposed post-repair attempt, not a blind solve. Before authoring the
program I had read and repaired the generator, studied the canonical rule, and
received an independent semantic review. A delayed final helper summary arrived
after challenge preparation but before program authoring; it repeated that
already-known repair information. This is recorded as earlier rule exposure.
From program authoring through check/finish I used only the prepared visible
challenge, my standalone Python program, and visible-only checker feedback.
No generator, Racket source, reference implementation, private label, or earlier
solution file was reopened during that authored attempt. No private query
outputs were accessed. These notes are a concise work log, not a token trace.

## Visible observations

Example 0: input8x10, output8x10. Only(0,5) and(7,6) become8. The vertical
three-yellow object stops at an occupied6 cell; its other end is filled. The
bottom-row horizontal triple has one off-grid end and one filled end. A diagonal
yellow singleton does not prevent filling that horizontal object. Other yellow
objects have a different size/shape and stay fixed; the vertical6 triple stays.

Example 1: input18x19, output18x19. Fourteen zeros become8. Both orientations
occur; isolated three-yellow bars get both caps where possible. An attached
fourth yellow cell makes a three-cell run ineligible. A nonyellow triple is
unchanged. Example2: input10x8, output10x8; only(1,4) and(3,2) become8. Its
color3 blocker and color3 bar are unchanged, supporting a fixed yellow target
rather than a color-relative rule.

Query inputs have dimensions9x20 and10x18; their output shapes and correctness
remain unknown to the checker. The hypothesis predicts unchanged dimensions.

## Revision1 and probes

Hypothesis: group yellow cells by cardinal adjacency. Only groups of exactly
three cells all in one row or column gain cyan at each empty, in-bounds endpoint.
Determine occupancy from the input, preserve all other values, and skip each
unavailable endpoint independently.

I wrote an independent set/stack flood fill with no imports from the generator
or shared runtime. A direct visible-only comparison against challenge.json
matched all three displayed outputs; exact dimensions and changed cells are in
visible_probe.json. Alternatives checked by those examples: capping every
three-cell run would change the attached-fourth-cell objects; capping every
color would change the nonyellow bars; 8-connectivity would merge the diagonal
singleton with a target; requiring two free caps would miss the one-sided cases.

Command from packet root: WORK/.venv-review/bin/python review.py solve check
--intent solve --note 'Cardinal yellow components of exactly three cells; extend each available endpoint independently from visible examples.'
No failed program was manufactured. This is the first authored revision.
