(rule! (lambda (g)
         (let* ((colors (filter (lambda (v) (!= 0 v))
                                (unique (map third (grid-cells g))))))
           (reduce (lambda (acc color)
                     (let* ((bb (bbox-of-cells (find-color g color)))
                            (r1 (first bb))
                            (c1 (second bb))
                            (r2 (third bb))
                            (c2 (fourth bb)))
                       (cellmap g
                                (r c v)
                                (if (and
                                      (>= r r1)
                                      (<= r r2)
                                      (>= c c1)
                                      (<= c c2)
                                      (zero? (at acc r c)))
                                    color
                                    (at acc r c)))))
                   g
                   colors))))