(rule!
  (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list (objects g 0))])
    (if (any? (lambda (p)
                (or (= (first p) 0) (= (first p) (- (rows g) 1))
                    (= (second p) 0) (= (second p) (- (cols g) 1))))
              (obj-cells obj))
        out
        (paint-cells out (obj-cells obj) (obj-color obj)))))