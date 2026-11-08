# Mark corners, then relay a selected frame

`finish_mode=mark_only` returns the exact canonical Racket program: mark the four
bounding-box corners of every yellow (`4`) component blue (`1`).

`finish_mode=selector_frame` performs that same operation as **step A**. The
resulting grid of newly blue corners is the input-dependent intermediate. A lone
red (`2`) selector scans right in that completed grid to the first blue corner;
the next blue corner in the same row and column identifies the selected box.
**Step B** paints the selected box's non-blue perimeter green (`3`). Skipping
step A leaves no blue corner for the selector, so the frame cannot be chosen.

The sampler keeps inputs identical across settings, supports 2–6 demonstrations
and 1–4 queries as stable prefixes, and always retains four novel queries. Every
scene has at least five irregular yellow objects; the selector target is neither
the smallest, largest, leftmost, nor rightmost object. The fourth query is a
substantive 30×30 scene. The bounded audit additionally rejects those four
object-rank shortcuts and a frame-all shortcut.

The adapter is reviewer-ready only. Native owner source review, qualification,
exact-source acceptance, and any later training admission remain separate.
