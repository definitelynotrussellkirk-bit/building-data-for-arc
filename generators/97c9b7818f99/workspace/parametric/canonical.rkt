(rule!
  (let ((seeds (filter (lambda (cell) (and (not (= (third cell) 0))
                                           (not (= (third cell) 8))))
                       (grid-cells g))))
    (define (dist cell r c)
      (+ (abs (- r (first cell))) (abs (- c (second cell)))))
    (define (fill-value r c)
      (let* ((dmin (apply min (map (lambda (cell) (dist cell r c)) seeds)))
             (nearest (filter (lambda (cell) (= (dist cell r c) dmin)) seeds)))
        (if (>= (length nearest) 2) 5 (third (first nearest)))))
    (for*/fold ([out g])
               ([r (in-range 1 (- (rows g) 1))]
                [c (in-range 1 (- (cols g) 1))])
      (if (= (at out r c) 0) (set-cell out r c (fill-value r c)) out))))