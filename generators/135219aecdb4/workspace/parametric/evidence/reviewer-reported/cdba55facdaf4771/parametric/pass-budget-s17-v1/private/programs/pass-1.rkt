(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((fill (lambda (grid)
                          (build-grid 4
                                      4
                                      (r c)
                                      (if (!= (at grid r c) 0)
                                          (at grid r c)
                                          (let* ((row-vals (filter (lambda (v) (!= v 0))
                                                                   (map (lambda (kc)
                                                                          (at grid r kc))
                                                                        (range 0 4))))
                                                 (col-vals (filter (lambda (v) (!= v 0))
                                                                   (map (lambda (kr)
                                                                          (at grid kr c))
                                                                        (range 0 4))))
                                                 (cands (filter (lambda (v)
                                                                  (and
                                                                    (not (member? v
                                                                                  row-vals))
                                                                    (not (member? v
                                                                                  col-vals))))
                                                                (range 1 5))))
                                            (if (= (length cands) 1) (first cands) 0)))))))
             (fill g)))))