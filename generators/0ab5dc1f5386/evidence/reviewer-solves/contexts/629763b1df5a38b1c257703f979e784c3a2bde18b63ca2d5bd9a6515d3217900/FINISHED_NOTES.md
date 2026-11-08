# Solve work log

## Prior exposure

I inspected this task's rule and generator before this required post-repair
solve, so this is not blind. During the solve episode I did not reopen the
Racket source, generator, reference outputs, private labels, or the preserved
prior solve. I used only `challenge.json`, my Python program, and visible check
feedback.

## Revision 1 hypothesis

Color-8 hollow rectangles are destination frames. Other nonzero 4-connected
components are source shapes, represented by their full bounding-box crops.
Process frames in row-major order and copy the first row-major source whose
height and width exactly match the frame interior. Preserve internal zero cells,
copy only nonzero values, retain source pixels, and do not rotate shapes.

The four visible demonstrations separately establish orientation-sensitive
matching, first-source tie breaking, multicolor/mask preservation, and source
retention. The third demonstration is especially diagnostic: it contains two
byte-identical loose 2x2 crops and two matching frames, but only the first frame
is filled. Therefore "used" is keyed by the complete crop value, not by source
component identity; a second equal occurrence is unavailable once that value
has been used.

Alternatives rejected from visible evidence: rotate-to-fit, choose the last
matching source, flatten a multicolor crop, reuse one source indefinitely, or
track duplicate equal crops as separate usable occurrences.

Remaining uncertainty before check: connected components that touch a frame are
not shown in this generated episode. Same-color frame detection plus ordinary
nonzero source extraction is the most direct interpretation of the examples.
