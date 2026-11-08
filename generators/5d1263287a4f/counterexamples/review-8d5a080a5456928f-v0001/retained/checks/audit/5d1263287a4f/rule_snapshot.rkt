(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((pw (/ (cols g) 3))) (build-grid h pw (r c) (at g r c))))))