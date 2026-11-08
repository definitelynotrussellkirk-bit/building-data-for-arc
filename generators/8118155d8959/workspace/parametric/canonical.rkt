(rule!
  (let* ((blues
           (sort
             (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0))
             (lambda (a b)
               (let ((sa (obj-size a))
                     (sb (obj-size b))
                     (ba (obj-bbox a))
                     (bb (obj-bbox b)))
                 (or (< sa sb)
                     (and (= sa sb)
                          (or (< (first ba) (first bb))
                              (and (= (first ba) (first bb))
                                   (< (second ba) (second bb))))))))))
         (small (first blues))
         (mid (second blues))
         (large (third blues)))
    (grid-from-fn h w
      (lambda (r c)
        (let ((v (cell-at g r c)))
          (cond
            [(any? (lambda (p) (and (= r (fst p)) (= c (snd p)))) (obj-cells small)) 2]
            [(any? (lambda (p) (and (= r (fst p)) (= c (snd p)))) (obj-cells mid)) 3]
            [(any? (lambda (p) (and (= r (fst p)) (= c (snd p)))) (obj-cells large)) 8]
            [else v]))))))