# Parametric assessment — d185ceed5cc1

The earlier left/right-gravity prototype was valid as a nearby variant but did
not make the packet's required input-dependent A→intermediate→B choice strong
enough. It is superseded by the native `packing_rule` family.

## Sequential dependency

- **Step A:** split each row at fixed color-8 walls and count the ordered
  nonzero pebbles in every maximal non-wall segment.
- **Intermediate:** the unique per-row count-argmax segment.
- **Step B:** pack that selected segment left and all other segments right,
  preserving pebble order.

Step B cannot choose its left-packed segment before Step A's counts are
compared. The retained protected-Racket counterfactual substitutes the widest
segment for the count argmax on the qualified 30×30 input and changes 420 final
cells.

The canonical default is not reformatted or reimplemented: `canonical.rkt` is
byte-identical to the selected authority. The finite teaching audit checks nine
plausible alternatives, not arbitrary programs. Owner exact-source acceptance
and any downstream training decision remain separate.
