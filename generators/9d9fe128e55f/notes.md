# Working notes: 9d9fe128e55f

## Base review

The existing `3.0.1` generator was retained unchanged. Protected Racket replay confirms its four ordinary schedule profiles and exact minimum/maximum override scenes agree with `rule_mirror`; all labeled canonical pairs also pass the exact selected program. The retained compact-shape limitation remains honest and does not block this parametric extension.

## Parametric design

`rank_policy` is episode-fixed. `all_by_size` returns the exact canonical Racket bytes. `right_anchor_threshold` selects the color-8 component with the greatest occupied column, binds its occupied cell count, discards smaller color-8 components, then size-ranks and recolors the survivors from the beginning of the legend. Thus step B cannot be determined without the input-derived intermediate from step A.

The adapter supports 2–6 demonstrations, defaults to 3, and always emits four distinct matched-input queries. The fourth query is a substantive 30×30 scene. The two-demo minimum contains crossed controls: fixed dimensions/right edge with thresholds 8 versus 6, and a later same-threshold geometry change.

## Adversarial findings and repairs

1. A randomly quarter-turned length-11 horizontal component became height 11 inside a height-10 profile. The root cause was treating declared line orientation as nuisance variation. Line styles now preserve orientation.
2. The initial lessons allowed a wrong minimum-column definition of “rightmost” and a fixed threshold of 6. Demo 1 was rebuilt with trap size 5, a smaller size-2 object, a size-7 near-threshold object, and the true size-8 anchor; both shortcuts now fail constructively.
3. Eight-connected components could fit all demonstrations for some seeds yet change a query. Demo 1 now guarantees diagonal-only contact between two separate 4-connected objects, killing that shortcut without increasing the two-demo minimum.

The task-local `adversarial_probe.py` replays these attacks across fresh seeds, the 2/3/6 count corners, both settings, all four queries, malformed request boundaries, ordinary/base boundary generation, and protected Racket labels. Finite rival elimination is not a uniqueness proof; owner source review and acceptance remain pending.
