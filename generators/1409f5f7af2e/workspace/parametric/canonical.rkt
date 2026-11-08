(rule!
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (if (and (> r 0) (< r (- (rows g) 1)) (= (at g r c) 0) (= (at g (- r 1) c) 3) (= (at g (+ r 1) c) 3))
          2
          (at g r c)))))