# Horizontal beams with an input-selected vertical relay

Status: **reviewer-ready native adapter; owner exact-source acceptance pending**.
The production generator and canonical Racket authority remain unchanged.

The episode-fixed parameter is `beam_mode`:

- `horizontal_only` — exact canonical/default behavior. Every seed casts its
  color horizontally through original zero cells until an edge or original seed.
- `dominant_relay` — first performs the same horizontal transform, then finds
  the unique most frequent nonzero color in that intermediate. Its original seed
  casts a vertical beam through original zero cells, stopping at an original seed
  or boundary. The vertical beam may overwrite horizontal paint where the input
  was zero.

The constructive family uses globally distinct seed colors, both dominant sides,
vertical blocker and no-blocker cases, matched inputs across settings, 2–6
independent demonstrations, and 1–4 queries. Ten deterministic slots are built
before slicing, so the first query is identical in one-query and four-query use.
The first query is a substantive 30×30 four-row case whose output spans all four
boundaries and quadrants.

## Sequential dependency

1. **A:** execute the canonical horizontal beam transform.
2. **Intermediate:** the input-dependent horizontal grid and its unique modal
   nonzero color, including that color's original seed position.
3. **B:** cast only that selected seed's color vertically through original zeros.

B cannot choose its color or anchor before A determines the modal horizontal
segment. The retained causal witness replaces that intermediate with the unique
least-frequent beam color and obtains a different protected-Racket output.

Public projections contain demonstration inputs/outputs and only the current
query input. Settings, programs, seeds, future query inputs, and query answers
remain private. Public filenames hash exact visible bytes.

## Verification snapshot

- 35/35 final staged changed-target tests and 27/27 focused native tests passed.
- Protected-Racket teaching audit passed for both settings against five executable
  rivals per setting; two content-addressed public challenges passed the strict
  saved-file checker.
- 50-seed sweep passed 500 episodes, 4,000 visible pairs, 250 matched-input
  comparisons, and 2,000 sequential public turns.
- Native qualification passed 4/4 jobs for both settings at seeds 0 and 17.
- The source-bound causal witness and an independent replay both passed.

Canonical/default program SHA-256:
`65a855ce11f7677687180f9efce9eaa4d834294153ea86cdc41c0a88e911ad02`.
Alternate program SHA-256:
`fd891abb3c01684a8f3813cb49de80a1a949a12dad5c764fea37664e5ba64fea`.
Prototype manifest SHA-256:
`417bfd62f2f5398fd4b2af8c5d4d54c335cccb836dd258be971e5fb1b16e9143`.

These are bounded reviewer checks. Owner acceptance and training admission have
not occurred; `training_admitted` remains false.
