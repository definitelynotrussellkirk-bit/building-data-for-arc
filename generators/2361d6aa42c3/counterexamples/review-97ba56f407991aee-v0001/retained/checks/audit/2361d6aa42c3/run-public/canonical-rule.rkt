(rule!
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (if (and (= (at g r c) 3)
               (= (count-where (lambda (d)
                                 (let ((nr (+ r (first d))) (nc (+ c (second d))))
                                   (and (in-bounds? nr nc (rows g) (cols g)) (= (at g nr nc) 3))))
                               cardinal-deltas)
                  1))
          2
          (at g r c)))))