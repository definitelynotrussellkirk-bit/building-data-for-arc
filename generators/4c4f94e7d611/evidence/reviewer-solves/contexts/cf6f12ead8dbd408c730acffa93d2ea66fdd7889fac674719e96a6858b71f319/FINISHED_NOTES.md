# Solve work log

## Exposure declaration

I saw the task's intended rule earlier while repairing its generator, so this is
an **exposed post-repair solve**, not a blind solve. During this solve episode I
kept the generator, Racket rule, reference solutions, private labels, and prior
solution explanations closed and used only the newly prepared visible examples.

## Revision 1 — component-size hypothesis

Across all four demonstrations, one 4-connected nonzero component is larger than
every other component. Its tight crop is the motif in the output. Every isolated
single-cell component, regardless of color, acts as one counter marker; connected
multi-cell distractors do not count.

Evidence from the visible examples:

- Example 0 has a four-cell color-6 motif and two singleton color-1 markers, so
  the output contains two motif copies.
- Example 1 has a five-cell color-6 motif, five singleton markers across colors
  2 and 5, and a two-cell color-1 distractor; the output contains five copies.
- Example 2 has a three-cell color-2 motif and three singleton markers, yielding
  three copies.
- Example 3 has a four-cell color-5 motif, one singleton marker, and a two-cell
  distractor, yielding one copy.

The copies are concatenated horizontally with one zero column between adjacent
copies. Their orientations alternate: original crop, left-right reflection,
original, and so on. This explains the asymmetric rows in examples 0–2 and is
not distinguishable from a plain copy in symmetric motifs.

Implementation plan: enumerate same-color, 4-connected nonzero components;
select the unique largest as the template; count all size-one components; render
only the template cells inside its bounding box; then concatenate the requested
number of alternating copies. Remaining uncertainty is limited to out-of-domain
cases such as tied largest components or zero singleton markers; neither occurs
in the visible lesson. The implementation uses a conservative one-copy fallback
for a marker-free grid.
