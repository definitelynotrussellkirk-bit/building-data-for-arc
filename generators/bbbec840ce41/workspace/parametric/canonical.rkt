(rule!
  (let ((n (rows g)))
    (for/fold ([out g]) ([cell (in-list (grid-cells g))])
      (let ((r (first cell)) (c (second cell)) (v (third cell)))
        (if (not (= v 0))
            (set-cell out (- n 1 c) (- n 1 r) v)
            out)))))