(rule!
  (let* ((sep (first (filter (lambda (c) (all? (lambda (r) (= (at g r c) 5)) (range 0 (rows g)))) (range 0 (cols g)))))
         (A (subgrid g 0 0 (- (rows g) 1) (- sep 1)))
         (B (subgrid g 0 (+ sep 1) (- (rows g) 1) (- (cols g) 1)))
         (h (max (rows A) (rows B)))
         (w (max (cols A) (cols B))))
    (grid-from-fn h w
      (lambda (r c)
        (let ((av (if (and (< r (rows A)) (< c (cols A))) (at A r c) 0))
              (bv (if (and (< r (rows B)) (< c (cols B))) (at B r c) 0)))
          (if (or (not (= av 0)) (not (= bv 0))) 7 0))))))
