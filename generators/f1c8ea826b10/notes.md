# Working notes: f1c8ea826b10

## Current decision

Retain a two-setting native family with episode-fixed `phase_anchor`:

- `bbox_top_left` is the exact canonical default, byte for byte.
- `minimum_marker` preserves wall-region discovery, solid singleton fills, and
  numeric min/max checker fills, but uses the input coordinate carrying the
  region's numeric minimum marker as the checker phase origin.

This is a deliberate A→intermediate→B composition. A selects the numeric minimum
marker and its coordinate in each multi-color region. That input-dependent
coordinate is the intermediate. B uses it to decide which parity class receives
the minimum color. A qualified protected-Racket witness substitutes the maximum
marker coordinate and changes 12 final cells.

## Sampler and teaching

The deterministic sampler builds one setting-neutral six-demo/four-query plan
and returns prefixes. It supports 2–6 demos and 1–4 queries; normal use has four
queries revealed sequentially. Both settings therefore receive identical inputs,
and direct one-query generation has the exact same first-turn public bytes as a
four-query lesson.

The first two demos reject the other setting and eight additional executable
shortcuts: maximum marker, row-major first/last marker, global origin, flipped
canonical phase, minimum-value parity, two-smallest palette, and solid minimum.
The finite audit executed all nine rivals on demos and queries for both settings
at seeds 0 and 17; no rival survived the demonstrations. This is finite evidence,
not universal program uniqueness.

Queries are 9×11, 15×17, 23×27 and a substantive 30×30. The 30×30 profile is a
separate lawful parametric extension with one seven-cell chamber dimension; the
unchanged production grammar remains capped at six-cell chambers and 29×29.

## Verification and limits

- Focused native tests: 10 passed.
- Complete staged task tests: 20 passed plus 15 subtests. The only warning is a
  pre-existing deprecated private provenance alias.
- Finite audit: four episodes, 242 protected-Racket evaluations, four exact
  hash-named public files, 25 negative cases, and 32/32 bounded Python seeds.
- Native qualification: two settings × seeds 0 and 17, two demos/four queries,
  32 protected-Racket evaluations.
- Causal witness: reviewer-replayed through protected Racket; wrong marker
  intermediate changes 12 output cells.

Production `generator.py`, the canonical ledger, and canonical authority are
unchanged. The original staged test's fixed-depth data lookup was repaired with
`reviewer_support.find_root` and `canonical_path`; no generator behavior changed.
The next required step is owner integration of these exact source bytes followed
by fresh native qualification and explicit acceptance. No training admission or
allocation change is claimed.
