# 269e22fb — current authoring decisions

## Rule
Treat the less frequent of the input's two colors as the emblem. The input is a
unique contiguous crop of one of the eight rotations/reflections of a fixed
20×20 geometric emblem. Recover the pose and crop offset, then render the full
pose in the input colors. This single blueprint-and-match rule covers all five
training pairs and both supplied test golds; it is not an input-to-output case
table.

## Parametric extension
`pocket_policy=preserve|mark_enclosed`. The canonical setting preserves the exact
reference program. The alternative performs the same crop localization and full
completion, then finds background cells not four-neighbor reachable from the
completed canvas boundary and recolors those enclosed pockets red. Step A is
pose/crop inference and completion; the completed 20×20 canvas is the
input-dependent intermediate consumed by step B's topology pass.

The family supports 2–6 demonstrations and four independently ordered queries.
Inputs are matched across settings and use unique crop dimensions/locations,
both reflected and unreflected poses, varied colors, and a 19×19 boundary case.
The source puzzle fixes a 20×20 output, so 30×30 stress is not lawful.

Owner registration, native qualification, exact-source acceptance and training
admission remain outside this reviewer return.
