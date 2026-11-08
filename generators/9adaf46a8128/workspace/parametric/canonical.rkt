(rule!
  (let ((dummy 0))
    (define sep (first (filter (lambda (r) (all? (lambda (v) (= v 5)) (row g r))) (range 0 (rows g)))))
    (define top (subgrid g 0 0 (- sep 1) (- (cols g) 1)))
    (define cells (filter (lambda (p) (not (= (at top (first p) (second p)) 0))) (grid-positions top)))
    (define bb (bbox-of-cells cells))
    (define template (subgrid top (first bb) (second bb) (third bb) (fourth bb)))
    (define out-h (- (rows g) sep 1))
    (define (transform marker)
      (cond [(= marker 1) template]
            [(= marker 2) (rotate-cw template)]
            [(= marker 3) (rotate-180 template)]
            [(= marker 4) (transpose template)]
            [else template]))
    (for*/fold ([out (empty-grid out-h (cols g) 0)])
               ([r (in-range (+ sep 1) (rows g))]
                [c (in-range (cols g))])
      (let ((marker (at g r c)))
        (if (member marker (list 1 2 3 4))
            (let* ((tr (transform marker))
                   (rr0 (- (- r (+ sep 1)) (quotient (rows tr) 2)))
                   (cc0 (- c (quotient (cols tr) 2))))
              (for*/fold ([acc out])
                         ([i (in-range (rows tr))]
                          [j (in-range (cols tr))])
                (let ((rr (+ rr0 i)) (cc (+ cc0 j)) (v (at tr i j)))
                  (if (and (not (= v 0)) (in-bounds? rr cc out-h (cols g)))
                      (set-cell acc rr cc v)
                      acc))))
            out)))))