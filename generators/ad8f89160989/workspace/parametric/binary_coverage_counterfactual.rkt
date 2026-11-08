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
              (let ((covered?
                     (any?
                      (lambda (seed)
                        (= (+ (abs (- r (first seed)))
                              (abs (- c (second seed))))
                           1))
                      seeds)))
                (if covered? 8 0))))))))
