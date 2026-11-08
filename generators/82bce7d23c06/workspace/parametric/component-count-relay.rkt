(rule!
  (lambda (g)
    (let* ((n (cols g))
           (nz (for/sum ((c (range 0 n)))
                 (if (!= (at g 0 c) 0) 1 0)))
           (sz (* nz n))
           (projected
             (build-grid sz
                         sz
                         (r c)
                         (let ((idx (+ (- c (- sz 1)) r)))
                           (if (and (>= idx 0) (< idx n))
                               (at g 0 idx)
                               0))))
           (component-count (length (objects-8 projected 0)))
           (source-cols
             (filter (lambda (c) (!= (at g 0 c) 0)) (range 0 n)))
           (target-col (list-ref source-cols (- component-count 1))))
      (build-grid sz
                  sz
                  (r c)
                  (let ((idx (+ (- c (- sz 1)) r)))
                    (if (= idx target-col)
                        9
                        (at projected r c)))))))
