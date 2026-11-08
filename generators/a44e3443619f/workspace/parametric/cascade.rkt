(rule!
  (let ((stage1
         (grid-from-fn (rows g) (cols g)
           (lambda (r c)
             (if (and (= (at g r c) 0)
                      (all? (lambda (d) (= (safe-at g (+ r (first d)) (+ c (second d)) 0) 2)) diagonal-deltas))
                 1
                 (at g r c))))))
    (grid-from-fn (rows stage1) (cols stage1)
      (lambda (r c)
        (if (and (= (at stage1 r c) 2)
                 (= (safe-at stage1 (+ r -1) (+ c -1) 0) 1)
                 (= (safe-at stage1 (+ r -1) (+ c 1) 0) 1)
                 (= (safe-at stage1 (+ r 1) (+ c -1) 0) 1)
                 (= (safe-at stage1 (+ r 1) (+ c 1) 0) 1))
            3
            (at stage1 r c))))))
