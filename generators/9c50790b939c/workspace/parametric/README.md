# Native `growth_delta` rail family

This directory retains the original source-bound authoring evidence and adds a
native adapter for ARC family `9c50790b939c`. The production generator and
canonical authority are unchanged.

The episode-fixed parameter is `growth_delta ∈ {0,1,2}`. Every setting finds the
unique mixed 8/9 source rail, derives its end-aligned 9-block length and the
unique all-8 rail exactly two cells longer, clears the source block, then paints
`source_block_length + growth_delta` cells on the matching target end.
`growth_delta=1` is byte-for-byte canonical.

The native generator supports independent 2–6 demonstration and 1–4 query
counts with stable prefixes and setting-neutral inputs. It stores four distinct
controller-side queries; public projection reveals one query at a time and
omits the setting, program, answer, future queries, and total-query hints. The
fourth query is a dense 30×30 rail scene with boundary contacts and distractor
lengths around the unique target length.

`self_audit.py` executes every retained rule through protected Racket, checks
Python parity, minimum-demo finite-rival elimination, matched inputs, count
prefixes, public first-turn stability, and 128-seed stress. `build_witness.py`
creates the qualification-bound causal witness used for owner replay.

The older `examples/` and `evidence/growth-delta-evidence.json` files remain as
traceable prototype evidence. They are not native qualification or training
admission.
