(rule!
  (let* ((cmd (at g 0 0))
         (cells (filter-cells g (lambda (r c v) (and (not (= v 0)) (not (and (= r 0) (= c 0)))))))
         (bb (bbox-of-cells cells))
         (sub (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
         (stage1 (cond [(= cmd 1) (rotate-cw sub)]
                       [(= cmd 2) (rotate-180 sub)]
                       [(= cmd 3) (flip-lr sub)]
                       [else (flip-ud sub)]))
         (cmd2 (at stage1 0 0)))
    (cond [(= cmd2 1) (rotate-cw stage1)]
          [(= cmd2 2) (rotate-180 stage1)]
          [(= cmd2 3) (flip-lr stage1)]
          [else (flip-ud stage1)])))
