(lambda (g)
  (let* ((h (rows g))
         (w (cols g)))
    (let* ((bg (at g 0 0))
           (dot (find-first (lambda (p) (!= (at g (fst p) (snd p)) bg))
                            (flatmap (lambda (r)
                                       (map (lambda (c) (cons r c)) (range 0 w)))
                                     (range 0 h))))
           (dr (fst dot))
           (dc (snd dot))
           (anti (= (+ dr dc) (- w 1)))
           (tc-c (if anti (- w 1) 0))
           (bc-c (if anti 0 (- w 1))))
      (cellmap g
               (r c v)
               (let ((v v))
                 (if (!= v bg)
                     v
                     (if (or
                           (and (= c dc) (< r dr))
                           (and
                             (zero? r)
                             (>= c (min dc tc-c))
                             (<= c (max dc tc-c)))
                           (and (= c dc) (> r dr))
                           (and
                             (= r (- h 1))
                             (>= c (min dc bc-c))
                             (<= c (max dc bc-c))))
                         1
                         v)))))))
