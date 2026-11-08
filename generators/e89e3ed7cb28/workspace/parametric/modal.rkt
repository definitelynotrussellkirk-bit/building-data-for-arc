(rule! (let ((dummy 0))
  (let* ((stage-a
          (for/fold ((out (empty-grid (rows g) (cols g) 0)))
                    ((c (in-range (cols g))))
            (let ((hits (filter (lambda (r) (not (= (at g r c) 0)))
                                (reverse (range 0 (rows g))))))
              (if (empty? hits)
                  out
                  (let ((r (first hits)))
                    (set-cell out r c (at g r c)))))))
         (survivor-colors
          (filter (lambda (color) (not (= color 0))) (grid-colors stage-a)))
         (key-color
          (first
           (sort survivor-colors
                 (lambda (a b)
                   (let ((ca (count-color stage-a a))
                         (cb (count-color stage-a b)))
                     (or (> ca cb) (and (= ca cb) (< a b)))))))))
    (grid-from-fn (rows g) (cols g)
                  (lambda (r c)
                    (if (= (at g r c) key-color) key-color 0))))))