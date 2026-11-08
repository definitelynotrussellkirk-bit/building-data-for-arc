(rule!
  (let ((div-col (find-first
                  (lambda (c) (for/and ([r (range 0 h)]) (= (at g r c) 8)))
                  (range 0 w))))
    (if div-col
        (for/fold ([out g]) ([p (find-color g 6)])
          (let* ((r (first p)) (c (second p)) (nc (- (* 2 div-col) c)))
            (if (in-bounds? r nc h w) (set-cell out r nc 6) out)))
        g)))