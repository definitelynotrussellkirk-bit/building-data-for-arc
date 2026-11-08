(rule!
  (let ((dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1))))
    (define seeds
      (filter (lambda (p) (not (= (at g (first p) (second p)) 0)))
              (grid-positions g)))
    (grid-from-fn
      (rows g)
      (cols g)
      (lambda (r c)
        (let ((original (at g r c)))
          (if (not (= original 0))
              original
              (let ((coverage
                     (length
                      (filter
                       (lambda (seed)
                         (= (+ (abs (- r (first seed)))
                               (abs (- c (second seed))))
                            1))
                       seeds))))
                (cond [(= coverage 0) 0]
                      [(= coverage 1) 8]
                      [else 1]))))))))
