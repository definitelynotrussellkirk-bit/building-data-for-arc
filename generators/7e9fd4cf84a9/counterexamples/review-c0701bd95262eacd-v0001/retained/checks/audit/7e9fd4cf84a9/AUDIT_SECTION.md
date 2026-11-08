## 7e9fd4cf84a9

**Disposition: needs repair; findings only.** Audited selected generator SHA-256
`f301010da4bc2f8bea1cac48693b3d08c7656bab617371d1082303130c86f015` against
canonical Racket rule hash `806f1d42e5ab`. The source remained unchanged. There
is no task-local `evidence/review_index.json`; current `notes.md` contains no
specific review decisions. No audit-target source, authority, or runtime was edited.

**Highest priority — the validator rejects every canonical input and generation
omits their preserved distractors.** All five canonical input/output pairs
agree with actual Racket execution, but `self_check` rejects each input as an
unexpected color: respectively 7, 1, 9, 4, and 5. Generated inputs contain only
0 and 3. A concrete wrong rival fills isolated zeros surrounded by green, then
erases all other colors to background. It matches Racket on **24/24 ordinary
generated calls** (seeds 0–5, index 0, all four bands including `None`) and on
**0/5 canonical pairs**. The first canonical pair gives a one-cell preservation
witness: Racket retains color 7 at zero-based position `(6,6)`, while the rival
erases it. Repair should admit canonical distractors, generate observable
preservation evidence, and test the corresponding rival. This finding concerns
the generator/validator domain; it is not a claim that the canonical rule is wrong.

**Declared degenerate textures violate the generator's validator; one is also
misdescribed as inert.** Calls `generate(0,0,texture=...)` with each of
`no_rectangles`, `complete_rect`, and `missing_on_border` return grids rejected
by `self_check`. Racket leaves the first two unchanged, but the last changes
cell `(2,3)` from 0 to 8. The canonical program scans every cell in each green
object's bounding box, including the border; it does not apply the
interior-only filter claimed by the generator's comment. Exact input, executed
output, and changed cell are retained in `report.json/degenerates`. Either remove
these out-of-domain public textures or define and validate their intended
semantics truthfully; do not silently treat `missing_on_border` as a no-op.

**The public axes are not realized reliably.** Six of the 24 ordinary calls
produce fewer rectangles than the `n_rectangles` recorded draw. Minimal examples:
`generate(3,0)` records three rectangles on a 9x9 grid but returns two green
components; `generate(3,0,difficulty="hard")` records five but returns four.
Both pass `self_check`; Racket fills exactly two and four cells respectively.
The bounded placement loop silently returns a partial scene. At seed 123,
index 0, all four `palette_kind` values and all four helpful `texture` values
produce exactly the same grid as the unoverridden call, and
`ctx.overrides_used()` is empty. Declared boundary overrides `grid_h=5`,
`grid_w=22`, and `n_rectangles=6` are rejected by narrower draw ranges. The
current axis contract therefore needs removal, explicit compatibility limits,
or actual support; requested rectangle counts should be constructed or fail
loudly rather than silently shrink.

**Evidence and scope.** Exact command and exit status are in
`checks/audit/7e9fd4cf84a9/commands.json`. The runnable reproducer is
`checks/audit/7e9fd4cf84a9/probe.py`; source/rule bindings, canonical results,
draw provenance, concrete grids, Racket outputs, and changed cells are in
`checks/audit/7e9fd4cf84a9/report.json`. The single probe exited 0 and executed
32 grids through the canonical Racket runtime: five canonical pairs, 24 ordinary
generated calls, and three declared degenerates. Exit 0 means the audit
reproductions completed; the findings remain unresolved. No full battery or
historical-return sweep was needed.
