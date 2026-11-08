(rule! (lambda (g)
         (let ((h (rows g))
               (w (cols g)))
           (grid-from-fn h
                         w
                         (lambda (r c) (if (and (= 1 (mod r 2)) (= 1 (mod c 2))) 0 1))))))