(rule!
  (let* ((colors
          (remove-duplicates
           (filter (lambda (v) (not (= v 0))) (apply append g))))
         (selected
          (first
           (sort colors
                 (lambda (a b)
                   (let ((ca (length (find-color g a)))
                         (cb (length (find-color g b))))
                     (if (= ca cb) (< a b) (> ca cb)))))))
         (mid
          (let ((dummy 0))
            (for*/fold ((out g))
                       ((r (in-range (- (rows g) 1)))
                        (c (in-range (- (cols g) 1))))
              (let ((v (at g r c)))
                (if (and (not (= v 0))
                         (= (at g r (+ c 1)) v)
                         (= (at g (+ r 1) c) v)
                         (= (at g (+ r 1) (+ c 1)) v))
                    (set-cell
                     (set-cell
                      (set-cell
                       (set-cell out r c v)
                       r (+ c 1) 0)
                      (+ r 1) c 0)
                     (+ r 1) (+ c 1) v)
                    out))))))
    (paint-cells mid (find-color mid selected) 8)))
