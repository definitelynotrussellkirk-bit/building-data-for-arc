# 70abd9105769 parametric family

`mode=canonical` is the selected canonical rule byte-for-byte: reduce every
filled odd square to its center cell.

`mode=majority_frame` is genuinely sequential:

1. Reduce every square to its center, preserving color.
2. Recount colors on that intermediate, so frequency means **number of square
   objects**, not input pixel area.
3. Select the unique object-majority color and draw a color-9 perimeter around
   the bounding box of its centers, preserving every center cell.

Every authored scene crosses object frequency against raw pixel frequency.  The
object-majority color has more squares, while a different color has more source
pixels because its fewer squares are larger.  Target centers also omit one outer
slot column, so framing all centers is visibly wrong.  The fourth query is a
substantive 30x30 boundary-touching stress case.

`semantic_sweep.py` cheaply attacks Python semantic shortcuts.  The protected
`adversarial_probe.py` executes the selected programs and Racket rivals and
retains exact counterexamples.  `skip_stage_a.rkt` is the causal ablation used by
the sequential-dependency witness.
