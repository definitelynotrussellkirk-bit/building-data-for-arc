(rule!
 (lambda (g)
   (let* ((h (quotient (rows g) 2))
          (w (cols g))
          (positions (grid-positions (empty-grid h w 0)))
          (upper-count
           (count-where
            (lambda (p) (not (zero? (at g (first p) (second p)))))
            positions))
          (lower-count
           (count-where
            (lambda (p) (not (zero? (at g (+ h (first p)) (second p)))))
            positions))
          (upper-sparser (< upper-count lower-count)))
     (build-grid
      h w
      (r c)
      (let ((upper (not (zero? (at g r c))))
            (lower (not (zero? (at g (+ r h) c)))))
        (if (if upper-sparser
                (and lower (not upper))
                (and upper (not lower)))
            6
            0))))))
