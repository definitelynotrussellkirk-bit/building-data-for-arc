(rule! (lambda (g)
         (let ((w (cols g)))
           (grid-from-fn 4
                         w
                         (lambda (r c)
                           (if (!= (zero? (at g r c)) (zero? (at g (+ r 5) c))) 3 0))))))