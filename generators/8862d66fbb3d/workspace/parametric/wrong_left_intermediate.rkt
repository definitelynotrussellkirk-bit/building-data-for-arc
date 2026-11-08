(rule!
  (let* ((left (subgrid g 1 0 3 2))
         (wrong
           (grid-from-fn 3 3
             (lambda (r c) (if (not (= (at left r c) 0)) 7 0)))))
    (grid-from-fn 3 3
      (lambda (r c)
        (if (and (= (at wrong r c) 7)
                 (or (and (> r 0) (= (at wrong (- r 1) c) 7))
                     (and (< r 2) (= (at wrong (+ r 1) c) 7))
                     (and (> c 0) (= (at wrong r (- c 1)) 7))
                     (and (< c 2) (= (at wrong r (+ c 1)) 7))))
            7
            0)))))
