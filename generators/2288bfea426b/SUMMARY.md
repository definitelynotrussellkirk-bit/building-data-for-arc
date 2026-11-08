# 2288bfea426b

One 4-connected red(2) prototype and 2-5 isolated markers. Marker colors encode
clockwise rotation: `1→0°`, `3→90°`, `4→180°`, `6→270°`. The unchanged Racket
rule normalizes the prototype bounding box and stamps every rotated copy in
cyan(8) onto a **fresh zero grid**; out-of-bounds stamp cells clip and overlaps
form a union.

Version `3.0.0` replaces dead/fake controls with four exact observable axes,
adds canonical-profile support in every difficulty band, and alternates broad
scenes with explicit teaching scenes containing all four codes plus a repeated
code. The teaching scene refutes single-code mapping errors and the two
canonical-fitting shortcuts “one stamp per code” and “only three markers.”

The independent oracle and audit CLI are in `workspace/reference_probe.py`;
Racket remains the label authority.
