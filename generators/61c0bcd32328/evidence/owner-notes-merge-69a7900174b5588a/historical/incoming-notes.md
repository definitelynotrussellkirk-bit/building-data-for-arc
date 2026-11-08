# Working notes: 61c0bcd32328

## Current repair

The selected generator remains the canonical clockwise corner-copy task. Version
`2.1.0` changes only the general-scene sampler: corner objects may now use the
one-cell shape as well as larger shapes. The previous `_SHAPES[1:]` choice made
singleton corner components unreachable even though the rule copies them, so an
`ignore_singleton_corner_components` shortcut was never taught. The retained
seed-0 `easy/single_tl` lesson contains a singleton at `(0,0)`; exact canonical
Racket copies it to `(0,9)`, while that shortcut leaves the grid unchanged.

Current selected-source SHA-256:
`4f45d334880485ba8e7926f352f6f9c919dad53df3a9b868af43703964dff4ec`.
The canonical rule source was not edited. Its exact SHA-256 remains
`0dc3328fe8ad885a19f7c620a4d641ffc733e8cc641a331d01b3e88410c5f64e`
and its normalized rule hash remains
`e3835c9a174e5fd8b8be9b2c3a7bd754629ce5f5197d6e25d7be704d40d32692`.

## Parametric proposal

`workspace/parametric/` is an unselected task-local prototype with one setting,
`direction ∈ {clockwise, counterclockwise}`, fixed once per episode. Clockwise
returns the canonical source byte-for-byte; counterclockwise changes only the
corner-to-corner translation. Each retained setting has three demonstrations
and four distinct queries. Exact Racket labels match all 14 stored pairs, every
demonstration refutes the opposite direction, all four queries are
setting-sensitive, and public challenge IDs hash only visible bytes.

Prototype SHA-256:
`ff6e6e8f2fdc5cd5ccdec9f57eee5854369b31bcb58952e7e20b898322732854`.
Verifier SHA-256:
`76ce1c21a0fb839faba39532e82c7bf31a56fa3bd13c420568c7573f61c90605`.
The proposal is evidence only: it does not select a variant, approve a source,
or admit training data.

## Measured limits and next action

The focused suite has 17 passing tests. The authored-scope adversarial pass
covered 192 finite episodes, three count schedules, both directions, all 12
single-corner profile/band cells within seeds `0..127`, public masking/ID
invariance, and invalid numeric/setting inputs. These are bounded checks, not a
proof over all seeds or all rival programs. The next useful maintainer action is
to replay the retained Racket verifier, decide whether the direction parameter
is worth selecting, and separately triage the source-bound peer finding in
`AUDIT.md`.
