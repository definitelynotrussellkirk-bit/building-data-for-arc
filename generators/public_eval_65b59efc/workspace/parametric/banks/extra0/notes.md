# Public parent 65b59efc: keyed template decoding

The first band contains n×n binary templates keyed by their source colors. The
middle band is a sparse n×n macro canvas; a token's color, not the panel that
happens to contain it, selects a template. The final band maps each source color
to an output color. Every token expands to its keyed template in the matching
macro cell and is recolored through that palette entry.

`binding_mode=self` is byte-identical to the canonical reference.
`binding_mode=next_token` binds each occupied row-major macro position to the
next occupied token cyclically before template and palette lookup. The sampler
supports n=3–5, 2–6 demonstrations, exactly four private queries, and a lawful
30-column profile whose output is 25×25. Equal-area but different templates and
panel/token decorrelation defeat position, area, and source-order shortcuts.

Authoring preflight and bounded audits are reviewer evidence only. Owner source
registration, native qualification, exact-source acceptance, and training
admission remain separate.
