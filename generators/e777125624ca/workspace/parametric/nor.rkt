(rule! (lambda (g)
         (build-grid (rows g)
                     3
                     (r c)
                     (if (and (zero? (at g r c)) (zero? (at g r (+ c 4)))) 8 0))))