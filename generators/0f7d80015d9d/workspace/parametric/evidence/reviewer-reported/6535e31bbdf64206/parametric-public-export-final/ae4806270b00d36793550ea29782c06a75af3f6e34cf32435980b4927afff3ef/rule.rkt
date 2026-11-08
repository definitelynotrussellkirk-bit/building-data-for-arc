(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g))
         ;; Positions of every gray(5) cell
         (grays (find-color g 5))
         ;; Bottom edge of the grays bbox
         (gr1 (max-list (map fst grays)))
         ;; Left edge of the grays bbox
         (gc0 (min-list (map snd grays))) (gc1 (max-list (map snd grays)))
         ;; Position of the first red(2) cell
         (red-cell (first (find-color g 2)))
         ;; Position of the first cyan(8) cell
         (cyan-cell (first (find-color g 8)))
         (mid-c (quotient (+ gc0 gc1) 2))
         (red-left (< (snd red-cell) mid-c))
         (new-cyan-c (if red-left (+ gc1 1) (- gc0 1))))
    (set-cell (set-cell (set-cell g
      (fst red-cell) (snd red-cell) 7)
      (fst cyan-cell) (snd cyan-cell) 2)
      gr1 new-cyan-c 8))))
