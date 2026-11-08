# Solve work log

Producer: agent — Claude (Opus 5.5), working in a Claude Code session. These notes are my own written summary, not a captured model conversation or token trace.

## Exposure before this step (not a blind solve)

I repaired this generator immediately before solving. I read the canonical Racket rule (`draw-rect-outline` over `objects`), the task's written solution and the four canonical pairs. I also wrote an independent Python oracle for the rule (`workspace/lesson_rivals.py`). I knew the rule before opening `challenge.json`. During this step I did not open the Racket rule, the generator, the oracle file, reference solutions or `.review/solve-private`. I am rewriting the program from the visible pairs, but my hypothesis came from that exposure, not from discovery.

## Reading challenge.json

- Train 0: a 4x3 block of 1s with one corner missing becomes a hollow 4x3 rectangle of 1s: interior cells (3,3) and (4,3) are cleared, and the missing corner (5,2) is filled. A 9-object (2x3 bbox) becomes a filled 2x3.
- Train 1: a single 7-object with a 3x3 bbox and a missing corner becomes a 3x3 ring; the center (1,7) is cleared.
- Train 2: a 4-object and a 1-object with 3x2 and 2x2 bboxes become filled boxes, which is also what their outlines are. A 3x4 8-object becomes a hollow ring.
- Each object keeps its color. Objects never touch, and colors are distinct within a grid.

## Revision 1 — deliberate teaching negative (`--intent teaching_negative`)

Hypothesis tested on purpose: "fill each object's bounding box". It fits every canonical pair, because every canonical bbox has a side of 2. I expect it to fail train 0, train 1 and the 8-object in train 2, because those demos show cleared interiors. This is the rival my generator repair targets. I am checking that the visible demos refute it. It is not an accidental failure.

Result of revision 1: executed, visible 0/3. All three demos refute filling: train 0 and train 1 clear interiors, and train 2's 3x4 8-object becomes a ring.

## Revision 2 — solve (`--intent solve`)

Hypothesis: on a blank canvas, for each same-color 4-connected component, draw the perimeter of its bounding box in its color. This keeps thin (2xk) boxes fully colored and clears hollow interiors, including blob cells inside them (train 0, train 1 center). I chose 4-connectivity and per-component rather than per-color boxes. The visible pairs cannot separate those readings because each color forms one component. I chose them from the written task description I had already read, not from these demos.

Remaining uncertainty: overlapping bboxes (never shown here) would depend on drawing order.
