(rule! (lambda (g)
         (let ((w (cols g)))
           (grid-from-fn 4
                         w
                         (lambda (r c)
                           (if (or (!= 0 (at g r c)) (!= 0 (at g (+ r 5) c))) 3 0))))))