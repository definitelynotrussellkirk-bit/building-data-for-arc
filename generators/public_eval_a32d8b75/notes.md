# Current source decision

This is a direct public-evaluation creation for parent `a32d8b75`.  The general
reference rule was inferred from all three supplied demonstrations and both
provided test golds, and every one of those five labels was executed through the
protected Racket runtime.

A full-height magenta column separates the widest central field from one or two
instruction sidebars.  Each sidebar contains a filled two-color texture swatch,
a monochrome glyph, a corner dot and a two-cell rotation bar.  The canonical
rule swaps the swatch colors, rotates the complete glyph as indicated, replaces
each glyph cell with the swapped swatch, and docks that sparse stamp at the
indicated field corner.  Empty glyph blocks remain transparent, preserving the
central field.  The hidden official case with two sidebars applies both stamps.
No supplied grid or answer is embedded in executable source.

The episode parameter is `scope=all|texture_indexed_component`.  `all` is the
exact canonical reference.  The alternate counts the swapped texture's new
top-left color, uses `(count - 1) mod component_count` to select one row-major
four-connected glyph component, then rotates and stamps only that component.
That selection is a genuine input-derived intermediate consumed by the later
rotation/tile/docking stage.

The matched sampler supports 2–6 demonstrations and four stored, distinct
queries.  It varies palettes, two- and three-cell textures, disconnected glyphs,
all four rotations and corners, one or two sidebars, patterned central fields,
and actual 30×30 inputs.  The first two demonstrations reject twelve declared
shortcut rules for both settings.  Query presentation is shuffled independently
through `adapter.presentation_order`; `adapter.public_view` emits one query with
no settings, program, answer or future input.

During protected preflight, seed 17 exposed a real parity defect: a selected
component was rotated inside the complete glyph canvas rather than its tight
crop.  A failing protected-Racket regression was retained, the selected mask was
normalized before sizing, and the full authoring preflight then passed.

Limits: the generated grammar uses five-column sidebars and 2×2/3×3 textures,
while the general reference also handles the supplied wider/5×5 official
sidebars.  Parsing intentionally rejects ambiguous central fields, malformed
controls, missing glyphs and stamps too large for the field.  Finite rival and
seed sweeps do not prove uniqueness against every possible program.

This is reviewer-ready authoring evidence only.  Owner registration, fresh
native qualification, exact-source acceptance and any training admission remain
separate pending gates.
