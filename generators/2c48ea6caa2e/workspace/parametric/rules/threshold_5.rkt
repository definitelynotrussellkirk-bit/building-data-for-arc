(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (bb (bbox-of-cells (find-color g 1)))
                (r1 (first bb))
                (c1 (second bb))
                (r2 (third bb))
                (c2 (fourth bb))
                (row-blues (map (lambda (r) (row-count g r 1)) (range 0 h)))
                (col-blues (map (lambda (c) (col-count g c 1)) (range 0 w))))
           (cellmap g
                    (r c v)
                    (if (= 1 v)
                        1
                        (if (and (>= r r1) (<= r r2) (>= c c1) (<= c c2) (zero? v))
                            (if (or (>= (nth row-blues r) 5) (>= (nth col-blues c) 5))
                                2
                                0)
                            0))))))