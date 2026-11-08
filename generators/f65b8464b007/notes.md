# Working notes: f65b8464b007

## Current parametric design

The native adapter preserves the exact canonical `shift_rule="next"` Racket
bytes and adds `shift_rule="densest_index"`. Inputs retain the original banded
cyclic-shift grammar. Step A counts occupied cells in each first-band section
and selects the unique densest shape; the zero-based section index is the
input-dependent intermediate. Step B uses that index as the cyclic source
offset for final-band shapes while preserving destination colors.

The alternative is deliberately non-collapsing: generated lessons vary the
densest index and keep it at least two, so neither a fixed one-step rule nor a
simple right/left shortcut survives. A bounded protected-Racket audit evaluates
eight declared rivals over matched three-demo/four-query episodes for both
settings; each intended setting is the sole demonstration survivor and every
other rival disagrees on at least one query. This is finite evidence, not a
universal uniqueness claim.

The family supports 2–6 demonstrations and exactly four distinct queries. The
largest stress query is 29x29 with substantive content; an exact 30x30 square is
not lawful because three-row bands separated by blank rows have height `4b+1`.
Native qualification is source-bound and passing. The causal witness replays a
qualified query with intermediate index 2 and shows that substituting the
canonical one-step program changes the final output. Reviewer status is ready;
owner integration, fresh qualification, and acceptance on exact live bytes are
still required before training admission.
