(rule!
  (list (map third (filter (lambda (cell) (not (= (third cell) 0))) (grid-cells g)))))