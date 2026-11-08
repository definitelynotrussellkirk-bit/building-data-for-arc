(rule!
  (let* ((cells2 (normalize-cells (find-color g 2)))
         (cells3 (normalize-cells (find-color g 3)))
         (both (append cells2 cells3)))
    (if (empty? both)
        (list (list 0))
        (let ((max-r (apply max (map first both)))
              (max-c (apply max (map second both))))
          (grid-from-fn (+ max-r 1) (+ max-c 1)
            (lambda (r c)
              (let ((p (list r c)))
                (cond [(and (member? p cells2) (member? p cells3)) 8]
                      [(member? p cells2) 2]
                      [(member? p cells3) 3]
                      [else 0]))))))))