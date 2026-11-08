(rule!
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (if (and (= (at g r c) 2)
               (all? (lambda (d)
                       (let ((nr (+ r (first d))) (nc (+ c (second d))))
                         (or (not (in-bounds? nr nc (rows g) (cols g))) (not (= (at g nr nc) 2)))))
                     cardinal-deltas))
          3
          (at g r c)))))