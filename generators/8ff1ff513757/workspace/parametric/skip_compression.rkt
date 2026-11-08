(rule!
 (grid-from-fn h w
   (lambda (r c)
     (let ((v (at g r c)))
       (if (and (!= v 0)
                (or (and (> r 0) (!= (at g (- r 1) c) 0))
                    (and (< r (- h 1)) (!= (at g (+ r 1) c) 0))))
           9
           v)))))
