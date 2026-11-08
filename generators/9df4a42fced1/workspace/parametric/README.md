# Native seeded-frame centers: canonical or center chain

`mode=canonical` returns the selected canonical Racket source byte-for-byte: each
hollow rectangular frame contributes one label at its floor-center, colored by
the frame's unique interior seed. `mode=center_chain` first executes that exact
reduction and then connects the resulting labels in row-major order. Each link
runs horizontally from the earlier center to the later center's column, then
vertically to the later center. Connector cells use color 1; derived labels are
never overwritten. Parametric inputs reserve color 1 for the chain.

The alternative is genuinely sequential. Step A produces an input-dependent
sparse grid of relocated seed labels. Step B discovers those derived positions,
sorts them, and chooses every path segment from them. Running B on the original
framed input does not expose the same point set; shifting the intermediate to the
original seed locations changes the path. The setting is fixed for the episode.

The deterministic bank is built before slicing and supports 2–6 demonstrations
and 1–4 queries. It contains ten distinct scenes with two or three frames,
off-center seeds, odd/even dimensions, varied palettes, and deterministic whole-scene
reflections that move the derived centers across seeds. Two substantive 30×30
scenes span all quadrants. Explicit settings share exactly
the same inputs. Qualification uses three demonstrations and four private
queries. Owner source review and native acceptance remain separate.
