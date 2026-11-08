(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((tile-size 5)
                  (tile-rows (list 0 6 12 18 24))
                  (tile-cols (list 0 6 12 18 24)))
             (build-grid tile-size
                         tile-size
                         (r c)
                         (let* ((values (for*/list ((tr tile-rows) (tc tile-cols))
                                          (at g (+ tr r) (+ tc c))))
                                (unique-vals (remove-duplicates values)))
                           (cond
                             ((= (length unique-vals) 1) (first unique-vals))
                             (else 1))))))))