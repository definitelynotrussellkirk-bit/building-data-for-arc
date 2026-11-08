(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((h (/ (rows g) 2)))
             (build-grid h
                         w
                         (r c)
                         (if (!= (zero? (at g r c)) (zero? (at g (+ r h) c))) 6 0))))))