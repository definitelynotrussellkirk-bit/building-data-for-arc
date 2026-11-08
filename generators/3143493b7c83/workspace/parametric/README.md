# Parametric family: contains vs exact bounding-box match

The exact canonical default extracts the 2×-upscaled marker bitmap and recolors
all 4-aligned lattice cells that **contain** its key offsets. The alternate
`exact_bbox` setting requires every location inside the extracted key bounding
box to equal the bitmap, so superpatterns remain unchanged.

Inputs are generated independently of the setting. Every lesson includes exact
matches, superpattern matches, count-preserving decoys, mirrored decoys and
partial-row decoys. Demonstrations alone must isolate one declared setting and
reject the bounded plausible-rival set in `prototype.py`. The fourth query is a
substantive 30×30 boundary case. Programs, settings and query labels stay private.

Sequential dependency: A extracts the input-specific key offsets from the marker;
B cannot know which offsets to test or recolor until A has produced that
intermediate. `verify.py` executes the correct, mirrored-intermediate and skipped-A
programs through protected Racket and records the changed final outputs.
