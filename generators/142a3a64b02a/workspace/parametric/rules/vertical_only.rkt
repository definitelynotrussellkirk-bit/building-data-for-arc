(rule!
  (reduce (lambda (out obj)
    (if (not (= (obj-color obj) 2)) out
      (let* ((cells (obj-cells obj))
             (rs (map fst cells))
             (cs (map snd cells))
             (r0 (min-list rs))
             (r1 (max-list rs))
             (c0 (min-list cs))
             (c1 (max-list cs)))
        (cond
          ((and #f (= r0 r1)) (set-cell (set-cell out r0 c0 4) r0 c1 4))
          ((= c0 c1) (set-cell (set-cell out r0 c0 4) r1 c0 4))
          (else out)))))
    g (objects g 0)))