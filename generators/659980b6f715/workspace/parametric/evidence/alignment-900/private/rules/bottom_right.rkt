(rule!
  (let* ((colors (filter (lambda (v) (not (= v 0))) (grid-colors g 0)))
         (c1 (first colors))
         (c2 (second colors))
         (n1 (normalize-cells (find-color g c1)))
         (n2 (normalize-cells (find-color g c2)))
         (h1 (+ 1 (apply max (map first n1))))
         (w1 (+ 1 (apply max (map second n1))))
         (h2 (+ 1 (apply max (map first n2))))
         (w2 (+ 1 (apply max (map second n2))))
         (out-h (max h1 h2))
         (out-w (max w1 w2))
         (a1 (map (lambda (p)
                    (list (+ (first p) (- out-h h1))
                          (+ (second p) (- out-w w1))))
                  n1))
         (a2 (map (lambda (p)
                    (list (+ (first p) (- out-h h2))
                          (+ (second p) (- out-w w2))))
                  n2)))
    (grid-from-fn out-h out-w
      (lambda (r c)
        (let ((p (list r c)))
          (cond [(and (member? p a1) (member? p a2)) 9]
                [(member? p a1) c1]
                [(member? p a2) c2]
                [else 0]))))))