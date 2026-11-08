# 41851e57e1a5 — bounding-box intersection

Version: `3.0.0`. Kind: `per_puzzle`. Racket authority unchanged:
`RULE_HASH = b8f48f4e78e4`.

On a zero background, one connected red(2) shape and one connected blue(1)
shape have overlapping inclusive bounding boxes and disjoint cells. One
isolated key cell has color 3..9. The output is a blank, same-size grid with
the entire bounding-box intersection filled in the key color, including
previously empty cells. Each shape has at least three cells; canonical
four/five-cell shapes and larger connected shapes are supported.

Defaults mix two informative area-fill examples with one compact example
every three draws. Compact motifs supply canonical size profiles, singletons,
lines, and small areas. Rich opposite-L shapes with optional teeth supply
3x3 through 5x5 overlaps, symmetries, and translated placements. Keys cycle
through all seven allowed colors. Exact integer controls: `grid_h` 8..20,
`grid_w` 8..20, and `key_color` 3..9. Legacy style controls are rejected.

The lesson contract covers three demonstrations plus one query and fourteen
declared rivals. The default consecutive-pair schedule supports every query
hold-out within a four-pair bundle; it does not establish universal induction.
See `notes.md` for domain, compatibility, and distribution limits, and
`workspace/README.md` for the executable evidence probe.

Approval remains derived from catalog policy and retained evidence; it is
not changed by a local passing check.
