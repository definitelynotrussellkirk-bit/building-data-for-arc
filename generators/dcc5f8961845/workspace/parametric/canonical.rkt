(rule!
  (let ((dummy 0))
    (define (apply-transform grid cmd)
      (cond [(= cmd 0) grid]
            [(= cmd 1) (rotate-cw grid)]
            [(= cmd 2) (rotate-180 grid)]
            [(= cmd 3) (transpose grid)]
            [(= cmd 4) (flip-lr grid)]
            [else (flip-ud grid)]))
    (let* ((cmd1 (at g 0 0))
           (cmd2 (at g 0 1))
           (clean (set-cell (set-cell g 0 0 0) 0 1 0))
           (obj (crop-to-content clean)))
      (apply-transform (apply-transform obj cmd1) cmd2))))