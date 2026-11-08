(rule! (lambda (g)
  ;; First find and paint the obstacle-aware shortest path.
  (let* ((pts (find-color g 2))
         (p1 (first pts))
         (p2 (second pts))
         (r1 (fst p1)) (c1 (snd p1))
         (r2 (fst p2)) (c2 (snd p2))
         (filled (shortest-path-fill g r1 c1 r2 c2 4 0))
         ;; The painted path is now a barrier.  Its removal partitions the
         ;; remaining walkable cells into off-path branch regions.
         (regions (find-0-regions filled 0))
         (largest (pick-max regions length))
         (marked (if largest (recolor-cells filled largest 8) filled)))
    ;; Preserve both endpoint markers after the two-stage transform.
    (set-cell (set-cell marked r1 c1 2) r2 c2 2))))
