(rule! (lambda (g)
  (let* ((pair-rows
          (filter
           (lambda (entry) (= (length (second entry)) 2))
           (map
            (lambda (r)
              (list r
                    (filter (lambda (c) (= (at g r c) 1))
                            (range 0 (cols g)))))
            (range 0 (rows g)))))
         (anchor (first (reverse pair-rows)))
         (anchor-cols (second anchor))
         (threshold (- (second anchor-cols) (first anchor-cols))))
    (for/fold ((out g)) ((entry pair-rows))
      (let* ((r (first entry))
             (cs (second entry))
             (span (- (second cs) (first cs))))
        (if (>= span threshold)
            (for/fold ((acc out))
                      ((c (in-range (first cs) (+ (second cs) 1))))
              (set-cell acc r c 1))
            out))))))
