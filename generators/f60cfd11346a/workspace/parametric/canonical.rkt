(rule!
  (let* ((seed (first (find-color g 2)))
         (region (connected-region g (first seed) (second seed) (lambda (r c v) (or (= v 0) (= v 2))) 4))
         (zeros (filter (lambda (p) (= (at g (first p) (second p)) 0)) region)))
    (paint-cells g zeros 8)))