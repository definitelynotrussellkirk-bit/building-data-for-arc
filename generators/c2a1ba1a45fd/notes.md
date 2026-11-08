# Working notes: c2a1ba1a45fd

## Current decision — review-c5c1d5a2104e19a1

Keep the selected generator and canonical rule unchanged. The native parametric
family adds one episode-fixed `object_order` parameter: exact canonical
`row_major` (default) versus `size_ascending`. Both settings use the same scenes,
source-color inference, 8-connected source objects, legend extraction, and
painting rule; only the input-derived object order changes.

The constructive lesson supports 2–6 demonstrations and 1–4 prefix-stable
queries. Every minimum lesson distinguishes the selected setting and the seven
declared rivals, including four-connectivity, legend-column order, source-color
legend inclusion, fixed first-dot recoloring, reverse row order, and descending
size. Four-query episodes end with a substantive 30×30 boundary case.

`audit_lessons.py` regenerates the bounded curriculum audit and canonical public
exports. The retained four-seed sweep covers 160 episodes with zero failures,
zero ambiguous settings, and zero surviving declared shortcuts. Eight public
files pass the independent saved-byte checker. Native qualification executed
both settings for seeds 0 and 17 through protected Racket. The causal witness
shows that substituting canonical row-major order for the selected size order on
the same qualified input changes the final grid.

Owner handoff: integrate the exact returned source, replay the packaged witness,
run fresh native qualification, and perform acceptance. Reviewer status is
`ready`; no acceptance or training admission is claimed.
