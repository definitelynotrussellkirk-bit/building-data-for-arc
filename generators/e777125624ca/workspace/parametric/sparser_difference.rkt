(rule! (lambda (g)
  (let* ((left-count
           (for*/sum ((r (in-range (rows g))) (c (in-range 3)))
             (if (zero? (at g r c)) 0 1)))
         (right-count
           (for*/sum ((r (in-range (rows g))) (c (in-range 3)))
             (if (zero? (at g r (+ c 4))) 0 1)))
         (sparser (if (< left-count right-count) 'left 'right)))
    (build-grid (rows g) 3 (r c)
      (let ((left (at g r c))
            (right (at g r (+ c 4))))
        (if (if (eq? sparser 'left)
                (and (zero? left) (not (zero? right)))
                (and (zero? right) (not (zero? left))))
            8
            0))))))
