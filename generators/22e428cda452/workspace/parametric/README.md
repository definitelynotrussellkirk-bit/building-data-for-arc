# Native parametric family: finish after corner projection

This directory contains the current native promotion candidate for
`22e428cda452`. It preserves the exact selected canonical Racket program as the
default and adds one episode-fixed sequential finish.

## Parameter

`finish` has two values:

- `project_only` — canonical/default. Erase each colored corner marker, project
  a 2×2 square inward from a top marker, and project a three-cell bent diagonal
  inward from a bottom marker. `canonical.rkt` is byte-for-byte the selected
  authority.
- `highlight_most_projected_color` — perform the complete canonical projection,
  count the projected cells belonging to each source color, and recolor every
  projected cell of the unique largest-total color with color `1`.

The alternative has an explicit A→B dependency:

1. **A:** erase the source markers and construct every side-dependent projected
   glyph.
2. **Intermediate:** the projected grid plus projected-cell totals by source
   color.
3. **B:** choose the unique maximum projected total and recolor that color's
   projected footprint.

The retained wrong-intermediate program instead counts source corner markers by
color, breaking ties by lower color. On the retained distinct-color witness,
that shortcut selects a bottom color while the true projected-footprint rule
selects the single top color; protected Racket changes seven final cells.

## Episode grammar

The adapter supports 2–6 demonstrations and 1–4 queries independently. Both
settings receive identical inputs. Every scene has orange (`7`) background,
three or four colored corner markers, at least one top marker, and both bottom
markers. Marker colors exclude the background and highlight colors.

The teaching prefix deliberately alternates two cases:

- all three colors are distinct, so the one top glyph wins by projected area
  even though source-marker counts tie;
- the two bottom markers share a lower-valued color, so their combined six-cell
  footprint beats the four-cell top glyph.

Later scenes include top/bottom diagonal sharing and four-corner color pairs.
This makes the winner depend on completed projection rather than a fixed top
branch, numeric color, first/last marker, or source frequency. The four-query
bank includes a 30×30 all-corner case with projected content near every corner.

## Files

- `adapter.py` — native generation contract, Python oracle, finite rival
  certificate, and dependency metadata.
- `promotion.json` — native adapter contract.
- `canonical.rkt` — byte-exact canonical/default program.
- `highlight_most_projected_color.rkt` — admitted alternative program.
- `highlight_most_source_markers.rkt` — non-admitted causal counterfactual.
- `audit.py` — reusable protected-Racket bounded audit for future reviewers.
- `evidence/current/self-audit.json` — current bounded authoring audit.

The prior `projection_inset` prototype remains as historical evidence only. It
is not the parameter declared by `promotion.json`.

## Retained checks and limits

The bounded audit covers seeds `0` and `17`, demo counts `2`, `3`, and `6`, all
four queries, both settings, matched inputs, prefix consistency, ten grid sizes
through 30×30, nine declared hypotheses, and 93 protected-Racket labels. Both
top-bearing and bottom-only winning colors occur. The portable task suite and
focused parametric suite are retained separately in packet checks/evidence.

These are finite deterministic checks. They do not prove universal
identifiability, measured learning benefit, owner acceptance, or training
admission. Public projections must use the shared exporter so settings,
programs, seeds, source indices, future queries, and answers remain private.
