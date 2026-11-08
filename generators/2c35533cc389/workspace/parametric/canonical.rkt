(rule!
 ;; Every red(2) gets a blue(1) painted immediately to its RIGHT (in bounds).
 (paint-cells g
              (filter (lambda (p) (< (second p) w))
                      (map (lambda (p) (list (first p) (+ (second p) 1)))
                           (find-color g 2)))
              1))