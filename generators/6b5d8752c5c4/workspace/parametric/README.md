# Divider-source parametric family

This family keeps the exact canonical program as `bbox_midpoint` and adds one
nearby setting, `lane_marker`. Both perform the same outward one-cell movement
of every color-9 cell; they differ only in how the divider is derived:

- `bbox_midpoint`: the long-axis midpoint of each object's bounding box.
- `lane_marker`: the colored marker in each short-axis lane.

The shared input grammar broadens the production bars by moving every lane
marker outside the central pair. The first two visible demonstrations therefore
separate the two settings and reject four named shortcuts. Episodes support
2–6 demonstrations and exactly four queries; the query schedule includes a
30x30 six-object stress case with both orientations and boundary contacts.

The native qualification path executes all labels with the protected Racket
runtime. Python mirrors are construction and audit aids only.

## Current reviewer evidence

- Focused contract: 24 tests passed.
- Bounded self-audit: 320 episodes across seeds 0–31, both settings, and every
  supported demonstration count; zero failures and no surviving named shortcut.
- Native protected-Racket qualification: four jobs (seeds 0 and 17 for both
  settings), 40 evaluations, and only the selected setting survived each
  demonstration set.
- Source-bound causal replay: replacing the bounding-box-midpoint intermediate
  with the lane-marker intermediate changed the final output.
- Portable staged target suite: 35 tests plus 217 subtests passed.

These are finite reviewer checks. Exact-source owner acceptance and downstream
training admission remain pending.
