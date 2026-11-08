(rule!
  (let* ((cmd (at g 0 0))
         (cells (filter-cells g (lambda (r c v) (and (not (= v 0)) (not (and (= r 0) (= c 0)))))))
         (bb (bbox-of-cells cells))
         (sub (subgrid g (first bb) (second bb) (third bb) (fourth bb))))
    (cond [(= cmd 1) (rotate-cw sub)]
          [(= cmd 2) (rotate-180 sub)]
          [(= cmd 3) (flip-lr sub)]
          [else (flip-ud sub)])))