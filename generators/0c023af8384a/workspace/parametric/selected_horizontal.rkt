(rule!
 (let* ((a (overlay g (flip-ud g)))
        (best
         (for/fold ((best (list 1 -1))) ((color (in-range 1 10)))
           (let ((count
                  (for*/fold ((n 0))
                             ((r (in-range (rows a)))
                              (c (in-range (cols a))))
                    (if (= (at a r c) color) (+ n 1) n))))
             (if (> count (second best)) (list color count) best))))
        (selected (first best)))
   (for*/fold ((out a))
              ((r (in-range (rows a)))
               (c (in-range (cols a))))
     (if (= (at a r c) selected)
         (set-cell out r (- (- (cols a) 1) c) selected)
         out))))
