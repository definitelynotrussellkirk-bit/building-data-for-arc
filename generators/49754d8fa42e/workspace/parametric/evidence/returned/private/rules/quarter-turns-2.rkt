(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((color (mode g 0)))
             (cond
               ((= color 1) (list (list 0 5 0) (list 5 5 5) (list 0 5 0)))
               ((= color 2) (list (list 0 5 0) (list 0 5 0) (list 5 5 5)))
               ((= color 3) (list (list 5 5 5) (list 5 0 0) (list 5 0 0)))
               (else (list (list 0 0 0) (list 0 0 0) (list 0 0 0))))))))
