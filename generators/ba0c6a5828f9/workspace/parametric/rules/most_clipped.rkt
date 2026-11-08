(rule!
  (lambda (g)
    (let* ((pivot (first (find-color g 2)))
           (pr (first pivot))
           (pc (second pivot))
           (markers (find-color g 1)))
      (define (rotations p)
        (let* ((dr (- (first p) pr))
               (dc (- (second p) pc)))
          (list (list dr dc)
                (list dc (- dr))
                (list (- dr) (- dc))
                (list (- dc) dr))))
      (define (visible-count p)
        (length
          (filter
            (lambda (d)
              (in-bounds? (+ pr (first d)) (+ pc (second d))
                          (rows g) (cols g)))
            (rotations p))))
      (define selected
        (foldl
          (lambda (p best)
            (if (< (visible-count p) (visible-count best)) p best))
          (first markers)
          (rest markers)))
      (foldl
        (lambda (d acc)
          (let ((nr (+ pr (first d)))
                (nc (+ pc (second d))))
            (if (in-bounds? nr nc (rows g) (cols g))
                (set-cell acc nr nc 1)
                acc)))
        g
        (rotations selected)))))
