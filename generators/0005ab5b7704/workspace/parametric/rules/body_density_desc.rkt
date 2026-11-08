(rule!
 ;; Stage A selects only header-marked columns and measures their body occupancy.
 (let ((keep (filter (lambda (c) (= (at g 0 c) 4)) (range 0 w))))
   (define (body-count c)
     (length
      (filter (lambda (r) (not (= (at g r c) 0)))
              (range 1 h))))
   ;; Stage B orders that selected-and-measured intermediate, then packs the body.
   (let ((ordered
          (sort keep
                (lambda (a b)
                  (let ((ca (body-count a))
                        (cb (body-count b)))
                    (or (> ca cb)
                        (and (= ca cb) (< a b))))))))
     (for/list ((r (in-range 1 h)))
       (for/list ((c (in-list ordered))) (at g r c))))))
