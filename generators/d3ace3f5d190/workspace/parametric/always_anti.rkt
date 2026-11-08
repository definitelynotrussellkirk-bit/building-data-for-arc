(rule!
  (let ((n (rows g)))
    (grid-from-fn n n
      (lambda (r c)
        (let* ((v (at g r c))
               (mirror (at g (- (- n 1) c) (- (- n 1) r))))
          (if (not (= mirror 0)) mirror v))))))
