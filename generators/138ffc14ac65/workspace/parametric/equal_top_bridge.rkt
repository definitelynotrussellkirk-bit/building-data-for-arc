(rule!
 (lambda (g)
   (let ((stage-a
          (for*/fold ((out (empty-grid (rows g) (cols g) 0)))
                     ((r (in-range (rows g)))
                      (c (in-range (cols g))))
            (let ((v (at g r c)))
              (if (= v 0)
                  out
                  (for/fold ((acc out)) ((rr (in-range 0 (+ r 1))))
                    (set-cell acc rr c v)))))))
     (for/fold ((out stage-a)) ((color (in-range 1 10)))
       (let ((hits
              (filter (lambda (c) (= (at stage-a 0 c) color))
                      (range 0 (cols stage-a)))))
         (if (= (length hits) 2)
             (for/fold ((acc out))
                       ((c (in-range (first hits) (+ (second hits) 1))))
               (set-cell acc 0 c color))
             out))))))
