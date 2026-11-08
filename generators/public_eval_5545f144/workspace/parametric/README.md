# Public waypoint completion family

`orientation=follow_final_leg|keep_initial_heading` is fixed for the episode.
The default is exactly `../../reference.rkt`. `adapter.generate(seed, settings,
demos=3, queries=4)` supports 2–6 demonstrations and 1–4 queries. The supported
training/export default is four queries. Settings, answers, and programs are private.

All ten inputs are sampled before slicing, preserving count prefixes and matching
settings. The first two demos differ in observed and final heading, defeat every
finite declared shortcut, and include a non-three-cell motif plus a nearest-point
choice. Queries use four distinct size profiles, including a lawful single-panel
30×30 scene with a real route; their profile order is seed-shuffled. Each returned
label is produced by Racket, with a separate Python diagnostic assertion.

Protected original-pair execution, finite rival checks, count-prefix checks,
public/private projection, and executed wrong-intermediate witnesses are retained
under task evidence. These are finite checks, not universal rule correctness.
