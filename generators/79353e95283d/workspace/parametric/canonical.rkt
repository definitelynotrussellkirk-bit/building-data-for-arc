(rule! (lambda (g)
         (build-grid (rows g)
                     3
                     (r c)
                     (if (and (= 1 (at g r c)) (= 1 (at g r (+ c 4)))) 2 0))))