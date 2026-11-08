# Working notes: 55ba26e599d3

The selected production rule draws the canonical rounded DDA between two red
endpoints, mapping path 0 to 2 and path 1 to 3. Its source and authority remain
unchanged by this parametric proposal.

## Parametric first-hit component family

Build the native adapter under `workspace/parametric/` with episode-fixed
`reach=line_only|first_blue_component`. The default returns the exact canonical
Racket text. The alternative finds the first input-blue hit along that DDA
(starting at the row-major first red endpoint), then recolors the complete
4-connected input-blue component containing that hit while retaining canonical
line drawing. The selected hit/component is an input-dependent intermediate;
off-path painting cannot be selected without it. No blue hit means line only.

The adapter uses matched inputs across settings, 2–6 demonstrations (default 3), independent
1–4 queries (normal request 4), deterministic query prefixes and substantive
5–30-cell grids. Construct demonstrations that separate the two settings and
plausible all-hit, last-hit, global-blue and connectivity shortcuts. Keep public
bytes restricted to demonstrations and query inputs using the existing helper.

The compulsory shallow and steep demonstrations reverse selected/later component
size order and include off-path arms and diagonal-only neighbors. The second
demonstration has interior endpoints: an independent review proved that using
only border endpoints allowed a line-to-edges rival to fit both demos but change
query 4 by 4 cells (canonical) or 20 cells (component variant). The repair keeps
the minimum at two demos. The before case is retained at
`checks/55ba26e599d3/extension-gap-before.json`; both regression cases failed before
the repair and now pass.

Current checks: 27 focused tests pass. The final protected-Racket self-review
executed 72 requests without failure, including minimum/maximum demo counts,
four distinct queries, substantive 30×30 cases and literal 5×5 stress. Fourteen
declared rivals were tested against the two- and three-demo lessons; only the
corresponding correct rule survived, with no query disagreements or execution
errors. This is finite evidence, not universal identifiability. Reproduction
and private examples are at `checks/55ba26e599d3/self-review-final/`; the native
inventory is `workspace/parametric/evidence/manifest.json`. Exact live-source
owner acceptance remains separate from reviewer qualification and training admission.

The existing canonical Python helper has a confirmed floating interpolation
operation-order mismatch. The protected-Racket reproducer found two output-cell
errors on each of a 12×23 fixture and its transpose; the proposed one-line fix
matched both references in memory. Its exact patch and replay are in
`workspace/rounding_proposal/`. The new prototype uses the correct operation
order without importing this helper. Applying the separate production repair
requires owner checks and canonical approval, then fresh qualification of any
parametric source binding that includes the changed generator.
