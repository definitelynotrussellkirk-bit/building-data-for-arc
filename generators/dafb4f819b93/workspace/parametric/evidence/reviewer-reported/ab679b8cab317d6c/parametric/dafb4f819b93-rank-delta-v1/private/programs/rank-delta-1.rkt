(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (ordered-colors
                 (remove-duplicates
                  (map (lambda (rr) (at g rr (- w 1)))
                       (range 0 h)))))
           (cellmap g
                    (r c v)
                    (if (!= 0 v)
                        v
                        (let* ((row-color (at g r (- w 1)))
                               (col-color (at g (- h 1) c))
                               (row-entry
                                (find (lambda (pair)
                                        (= (second pair) row-color))
                                      (enumerate-list ordered-colors)))
                               (col-entry
                                (find (lambda (pair)
                                        (= (second pair) col-color))
                                      (enumerate-list ordered-colors))))
                          (if (= 1 (- (first row-entry) (first col-entry)))
                              row-color
                              0)))))))