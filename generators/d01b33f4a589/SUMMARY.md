# d01b33f4a589 — Corner-Command Tiling

Read the four corner cells as transform commands, crop the non-corner motif,
transform it once per corner in reading order, and pack the four variants into
a 2-by-2 output. Commands are 1=clockwise 90°, 2=180°, 3=left/right reflection,
and 4=up/down reflection. Motif colors may equal command colors: corners are
excluded by position, not by value.

Kind: `per_puzzle`. Current version: `3.1.0` (imported baseline `3.0.0`).
Approval is derived by the catalog from current code and retained evidence.

Every four consecutive **unconstrained** draws with the same seed/difficulty
contain an asymmetric L4 example with all four commands in a non-public order.
It distinguishes the twelve single-command-alias competitors and the public
profile/order shortcut. This is a finite, declared lesson contract, not a proof
of uniqueness over all possible programs or a measured model-accuracy gain.
Explicit axis overrides take precedence; short or arbitrarily reassembled
lessons do not receive this guarantee.

All five original canvas/motif profiles and both command multisets remain.
Ordinary slots preserve difficulty weighting, orientation, position and color
variation; approximately 5% of the overall default distribution retains literal
public inputs. One quarter of slots now prioritize instruction over independent
marginal sampling. See `notes.md` and `workspace/README.md` for reproduction.
The canonical Racket program is unchanged; a comment-only archival selected-rule
text drift was synchronized to its existing raw/canonical source.
