(rule!
  (let ((codes (filter (lambda (v) (member v (list 1 2 3 4))) (first g)))
        (motif (crop-to-content (subgrid g 1 0 (- (rows g) 1) (- (cols g) 1)))))
    (define (tf code)
      (cond [(= code 2) (rotate-cw motif)]
            [(= code 3) (rotate-180 motif)]
            [(= code 4) (rotate-cw motif)]
            [else motif]))
    (define grids (map tf codes))
    (define out-h (apply max (map rows grids)))
    (define out-w (+ (apply + (map cols grids)) (max 0 (- (length grids) 1))))
    (let pack ([remaining grids] [left 0] [out (empty-grid out-h out-w 0)])
      (if (empty? remaining)
          out
          (let* ((grid (first remaining))
                 (next (for*/fold ([acc out])
                                   ([r (in-range (rows grid))]
                                    [c (in-range (cols grid))])
                         (let ((v (at grid r c)))
                           (if (not (= v 0)) (set-cell acc r (+ left c) v) acc)))))
            (pack (rest remaining) (+ left (cols grid) 1) next))))))