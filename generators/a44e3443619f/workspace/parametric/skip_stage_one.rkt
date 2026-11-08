(rule!
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (if (and (= (at g r c) 2)
               (= (safe-at g (+ r -1) (+ c -1) 0) 1)
               (= (safe-at g (+ r -1) (+ c 1) 0) 1)
               (= (safe-at g (+ r 1) (+ c -1) 0) 1)
               (= (safe-at g (+ r 1) (+ c 1) 0) 1))
          3
          (at g r c)))))
