(rule!
 ;; Sort the rows by their non-zero cell count, densest first.
 (sort g (lambda (a b) (> (count-where (lambda (v) (!= v 0)) a) (count-where (lambda (v) (!= v 0)) b)))))