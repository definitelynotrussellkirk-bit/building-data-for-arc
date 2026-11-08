(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (build-grid 5
                       w
                       (r c)
                       (let ((top (at g r c))
                             (bot (at g (+ r 6) c)))
                         (if (!= bot 0) bot top))))))