(rule!
  (let* ((cells (filter-cells g (lambda (r c v) (and (not (= v 0)) (not (and (= r 0) (= c 0)))))))
         (bb (bbox-of-cells cells))
         (sub (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
         (cmd2 (at sub 0 0)))
    (cond [(= cmd2 1) (rotate-cw sub)]
          [(= cmd2 2) (rotate-180 sub)]
          [(= cmd2 3) (flip-lr sub)]
          [else (flip-ud sub)])))
