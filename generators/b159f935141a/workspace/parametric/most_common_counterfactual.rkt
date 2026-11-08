(rule!
 (let* ((records
         (for*/fold ((acc (list)))
                    ((r (in-range 1 (- (rows g) 1)))
                     (c (in-range 1 (- (cols g) 1))))
           (let ((arms (list (at g (- r 1) c)
                             (at g (+ r 1) c)
                             (at g r (- c 1))
                             (at g r (+ c 1)))))
             (if (and (= (at g r c) 0)
                      (!= (first arms) 0)
                      (all? (lambda (v) (= v (first arms))) arms))
                 (cons (list r c (first arms)) acc)
                 acc))))
        (colors (remove-duplicates (map third records)))
        (selected
         (pick-max colors
                   (lambda (color)
                     (count-if (lambda (record) (= (third record) color)) records)))))
   (for/fold ((out g)) ((record records))
     (if (= (third record) selected)
         (set-cell out (first record) (second record) selected)
         out))))