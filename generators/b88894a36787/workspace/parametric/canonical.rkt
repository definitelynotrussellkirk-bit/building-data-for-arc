(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (header (filter (lambda (c2) (!= (at g 0 c2) 0)) (range 0 w)))
                (header-colors (map (lambda (c2) (at g 0 c2)) header))
                (dots (filter (lambda (x) x)
                              (for*/list ((r (range 1 h)) (c2 (range 0 w)))
                                (and (!= (at g r c2) 0) (list r c2 (at g r c2))))))
                (entries (for/list ((i (range 0 (length header))))
                           (let* ((hc (list-ref header i))
                                  (hcol (list-ref header-colors i))
                                  (dot (find (lambda (d) (= (third d) hcol)) dots)))
                             (list hc
                                   hcol
                                   (if dot (first dot) (- h 1))
                                   (and dot (second dot)))))))
           (cellmap g
                    (r c v)
                    (let* ((match (find (lambda (e)
                                          (let* ((ecol (first e))
                                                 (ecolor (second e))
                                                 (trow (third e))
                                                 (tcol (fourth e)))
                                            (or
                                              (and (= c ecol) (<= r trow))
                                              (and
                                                tcol
                                                (= r trow)
                                                (if (< tcol ecol)
                                                    (and (>= c tcol) (<= c ecol))
                                                    (and (>= c ecol) (<= c tcol)))))))
                                        entries)))
                      (if match (second match) 0))))))