(rule!
  (let ((dummy 0))
    (define p1 (first (find-color g 1)))
    (define p2 (first (find-color g 2)))
    (define dr (- (first p2) (first p1)))
    (define dc (- (second p2) (second p1)))
    ;; Wrong order: the connected source is selected before clipping splits it.
    (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([p (in-list (find-color g 3))])
      (let ((rr (+ (first p) dr)) (cc (+ (second p) dc)))
        (if (in-bounds? rr cc (rows g) (cols g))
            (set-cell out rr cc 4)
            out)))))
