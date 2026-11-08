(rule!
  (let ((totals (map (lambda (color) (length (find-color g color))) (list 1 2 3))))
    (grid-from-fn 6 3
      (lambda (r c)
        (let ((color (+ c 1))
              (hgt (list-ref totals c)))
          (if (>= r (- 6 hgt)) color 0))))))