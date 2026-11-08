(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (/ (rows g) 2)))
             (build-grid hh
                         w
                         (r c)
                         (if (or (and (!= (at g r c) 0) (= (at g (+ r hh) c) 0)) (and (= (at g r c) 0) (!= (at g (+ r hh) c) 0))) 4 0))))))