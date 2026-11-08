# Native parametric family: canonical winner vs crossing follower

`paint_target=winner` returns the selected canonical program byte-for-byte. The
alternative performs a causal composition:

1. **A — canonical rank:** enumerate both downward diagonal run directions and
   select the canonical highest-scoring run.
2. **Intermediate:** the winner's exact input-derived cell set, direction and
   length.
3. **B — crossing follower:** among strictly shorter runs in the opposite
   direction that intersect those winner cells, select the highest canonical
   score and paint it cyan.

Every generated board contains a stronger global runner-up and a stronger
non-crossing opposite-direction run, so neither shortcut produces the follower.
The six templates cover winner lengths 6, 7 and 8 in both directions. Random
blockers retain the reviewed dense, one-component, gray-bordered 10×10 grammar.

The supported API is 2–6 demonstrations and 1–4 queries independently. Native
qualification uses four queries. The family intentionally remains 10×10: all
five canonical pairs and the approved generator grammar are fixed 10×10, so a
30×30 extension would broaden the source domain without authority rather than
stress the same admitted grammar.

## Public controller projection

`public_challenge(episode)` uses the packet's canonical
`reviewer_support.public_challenge_bytes` projection: demonstration inputs and
outputs remain visible, while each query exposes only its input. Settings,
seeds, Racket source and query answers are ignored by that projection and cannot
change its content ID. `controller_turns(episode)` returns one such query per
turn with no future-query or total-count field. Its first turn is byte-identical
to generating the same seed/setting with `queries=1`.
