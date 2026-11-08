(rule! (lambda (g)
  ;; Color 2 marks the two path endpoints.
  (let* ((pts (find-color g 2))
         (p1 (first pts))
         (p2 (second pts))
         (r1 (fst p1)) (c1 (snd p1))
         (r2 (fst p2)) (c2 (snd p2))
         ;; Paint the shortest route through color-0 cells with color 4.
         (filled (shortest-path-fill g r1 c1 r2 c2 4 0)))
    ;; Preserve both endpoint markers.
    (set-cell (set-cell filled r1 c1 2) r2 c2 2))))