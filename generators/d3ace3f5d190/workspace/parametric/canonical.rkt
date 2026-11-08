(rule!
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (let ((v (at g r c)) (mirror (at g c r)))
        (if (not (= mirror 0)) mirror v)))))