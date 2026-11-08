(rule!
  (let* ((colors (filter (lambda (v) (not (= v 0))) (grid-colors g 0)))
         (c1 (first colors))
         (c2 (second colors))
         (n1 (normalize-cells (find-color g c1)))
         (n2 (normalize-cells (find-color g c2)))
         (both (append n1 n2)))
    (let ((max-r (apply max (map first both)))
          (max-c (apply max (map second both))))
      (grid-from-fn (+ max-r 1) (+ max-c 1)
        (lambda (r c)
          (let ((p (list r c)))
            (cond [(and (member? p n1) (member? p n2)) 9]
                  [(member? p n1) c1]
                  [(member? p n2) c2]
                  [else 0])))))))