(rule! (lambda (g)
         (let ((h (rows g))
               (w 3))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (if (= 1 (+ (if (!= 0 (at g r c)) 1 0) (if (!= 0 (at g r (+ c 4))) 1 0))) 2 0))))))