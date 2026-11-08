(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((h (/ (rows g) 2)))
             (build-grid h
                         w
                         (r c)
                         (if (and (not (zero? (at g r c))) (not (zero? (at g (+ r h) c)))) 3 0))))))
