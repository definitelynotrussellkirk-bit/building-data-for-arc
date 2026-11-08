(rule!
  (let* ((guides (find-color g 5))
         (work (grid-from-fn (rows g) (cols g)
                 (lambda (r c)
                   (let ((v (at g r c)))
                     (if (and (not (= v 0)) (not (= v 5))) v 0))))))
    (define mirrored
      (if (and (= (length guides) 2) (= (first (first guides)) (first (second guides))))
          (for*/fold ([out work])
                     ([r (in-range (rows g))]
                      [c (in-range (cols g))])
            (let ((v (at work r c)))
              (if (not (= v 0)) (set-cell out (- (- (rows g) 1) r) c v) out)))
          (for*/fold ([out work])
                     ([r (in-range (rows g))]
                      [c (in-range (cols g))])
            (let ((v (at work r c)))
              (if (not (= v 0)) (set-cell out r (- (- (cols g) 1) c) v) out)))))
    (paint-cells mirrored guides 5)))