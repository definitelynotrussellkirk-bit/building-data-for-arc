# Native parametric family: key-matched endpoint segments

`connection_mode=all_aligned` is the byte-exact canonical rule: every color
with exactly two row- or column-aligned cells is completed into its inclusive
segment.

`connection_mode=key_match` adds an input-dependent sequence. Step A reads the
orientation and inclusive length of the color-7 key pair. Step B completes the
key and exactly those other pairs with the same orientation and length, while
preserving nonmatching pairs, diagonal pairs, singletons and multi-cell texture.
Every lesson includes independent same-orientation and same-length controls.

The adapter supports 2–6 demonstrations and exactly four private queries. The
fourth query is a substantive 30×30 case with more than 90 foreground cells.
