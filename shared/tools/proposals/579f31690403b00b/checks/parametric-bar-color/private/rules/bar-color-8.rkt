(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (let* ((non7 (filter (lambda (c2) (!= (at g r c2) 7)) (range 0 w)))
                           (c6-pos (find (lambda (c2) (= (at g r c2) 6)) non7)))
                      (if c6-pos
                          (let* ((count (length non7))
                                 (idx (count-if (lambda (c2) (< c2 c6-pos)) non7))
                                 (bar-start (- c6-pos idx))
                                 (bar-end (+ bar-start (- count 1))))
                            (if (and (>= c bar-start) (<= c bar-end)) 8 7))
                          7))))))