(rule!
  (let* ((items
           (sort (map (lambda (obj) (list (obj-size obj) (obj-color obj))) (objects g 0))
                 (lambda (a b)
                   (cond [(not (= (first a) (first b))) (> (first a) (first b))]
                         [else (< (second a) (second b))]))))
         (row (apply append (map (lambda (item) (make-list (first item) (second item))) items))))
    (if (empty? row) (list (list 0)) (list row))))