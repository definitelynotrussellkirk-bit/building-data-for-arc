# Post-repair solve: c39bef185e7e

## Exposure and scope

Earlier rule exposure: **yes**. I had inspected and repaired this generator,
including its selected Racket authority, before this episode. This is an exposed
solve, not a blind discovery. From `solve_episode.py prepare` until finishing,
I consulted only the public challenge/presentation and my new Python program.
I did not reopen the generator, rule, previous solutions, canonical labels,
or private query data. These are reviewer-authored work-log notes, not a
captured token-level model trace.

## Visible hypothesis

The earlier-exposed hypothesis is: group green, orthogonally connected objects
by shape up to translations, rotations, and reflections, then recolor the one
singleton class to 8. Preserve the other objects, background, and corner marker.

Example 0 has input/output 10 x 12 and four equal-sized green objects; only
the upper-left object changes. Example 1 has input/output 10 x 12 and four
five-cell objects; the upper-right object changes. Example 2 has input/output
11 x 12 and three four-cell objects; the lower-left object changes. Equal size
in these visible examples rules out selecting solely by object cell count.
Their varying answer locations rule out a fixed location. The non-green
corner marker remains unchanged in every pair.

## Revision 1 and probes

I wrote a fresh flood-fill implementation for color 3 and enumerated the eight
signed coordinate permutations to obtain a translation-normalized shape key.
Count each key's multiplicity and paint the sole singleton's original cells.
The implementation does not import any project code. The visible-only probe
in `visible_probe.json` found class multiplicities [1,3], [1,3], and [1,2],
and exact agreement on all changed cells in the three demonstrations.
The provided checker completed revision 1: 3/3 visible examples passed and
both query executions completed. Hidden query correctness remains unknown.

No failed attempt was manufactured. Query outputs and their dimensions are
unknown, and the checker intentionally withholds their correctness.

I stopped after that successful visible check because no visible evidence
requires another hypothesis. The final declaration preserves earlier exposure
and records no reference consultation during this solve phase.
