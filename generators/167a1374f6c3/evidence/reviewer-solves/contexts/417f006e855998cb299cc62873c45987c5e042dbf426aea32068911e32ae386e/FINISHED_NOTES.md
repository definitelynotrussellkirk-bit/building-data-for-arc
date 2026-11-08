# Solve work log

## Exposure declaration

I had already inspected the assigned task's generator and canonical authority during the repair, so this is **not blind**. During this solve episode I consulted only `solve/challenge.json`, my own test, and the solve checker; I did not reopen the generator, Racket rule, reference outputs, or private labels.

## Visible-example hypothesis

The nonzero prefix of row 0 is an ordered program. The colored object below row 0 is tightly cropped. The output is a left-to-right timeline containing the initial crop and one cumulative state after each program code, with one zero column between panels and all panels aligned to the top.

From visible train pair 2, code 3 turns the asymmetric 3x3 crop counterclockwise and code 2 then turns that result 180 degrees. Train pairs 1 and 3 distinguish the remaining mappings: code 1 is clockwise rotation and code 4 is a left-right reflection. Repeated codes in train pair 1 show that operations are cumulative rather than independently applied to the initial crop.

## Alternatives checked

- Applying each code independently to the initial crop fails the repeated/noncommuting timelines.
- Omitting the initial crop makes every visible output one panel too short.
- Bottom-aligning rectangular panels disagrees with the top-aligned visible galleries.
- Reading nonzeros beyond the first zero in row 0 is unsupported; all examples use a contiguous prefix and then stop.

## Test-first probe

I wrote `solve/test_visible.py` against the untouched skeleton and observed the expected `NotImplementedError`. I then implemented crop, the four transforms, cumulative execution, and top-aligned packing. No deliberate negative revision was manufactured.
