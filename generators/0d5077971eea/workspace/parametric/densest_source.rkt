(rule!
  ;; Select the eligible row with the most interior cyan markers, bind its
  ;; leading header color, then use that input-derived color for every marker.
  (let ((dummy 0))
    (define (marker-count r)
      (count-where (lambda (c) (= (at g r c) 8)) (range 1 w)))
    (define eligible
      (filter (lambda (r)
                (and (!= (at g r 0) 0)
                     (!= (at g r 0) 8)
                     (> (marker-count r) 0)))
              (range 0 h)))
    (if (empty? eligible)
        g
        (let* ((source
                 (foldl (lambda (r best)
                          (if (> (marker-count r) (marker-count best)) r best))
                        (first eligible)
                        (rest eligible)))
               (key (at g source 0)))
          (grid-from-fn h w
            (lambda (r c)
              (let ((v (at g r c)))
                (if (and (> c 0) (= v 8)) key v))))))))
