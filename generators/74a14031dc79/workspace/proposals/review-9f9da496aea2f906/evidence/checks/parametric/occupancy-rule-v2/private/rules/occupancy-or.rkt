(rule! (lambda (g)
         (let ((h (rows g))
               (w 3))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (if (or (!= 0 (at g r c)) (!= 0 (at g r (+ c 4)))) 2 0))))))