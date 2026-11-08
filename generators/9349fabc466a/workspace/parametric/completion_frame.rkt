(rule!
  (let ((colors (grid-colors g 0)))
    (define (span-stage)
      (grid-from-fn (rows g) (cols g)
        (lambda (r c)
          (let ((v (at g r c)))
            (if (not (= v 0))
                v
                (let ((fill-color
                        (find-first
                          (lambda (color)
                            (let ((pts (find-color g color)))
                              (or
                                (any?
                                  (lambda (p1)
                                    (any?
                                      (lambda (p2)
                                        (and (= (first p1) r) (= (first p2) r)
                                             (<= (min (second p1) (second p2)) c)
                                             (<= c (max (second p1) (second p2)))))
                                      pts))
                                  pts)
                                (any?
                                  (lambda (p1)
                                    (any?
                                      (lambda (p2)
                                        (and (= (second p1) c) (= (second p2) c)
                                             (<= (min (first p1) (first p2)) r)
                                             (<= r (max (first p1) (first p2)))))
                                      pts))
                                  pts))))
                          colors)))
                  (if fill-color fill-color 0)))))))
    (define stage (span-stage))
    (define positions (grid-positions g))
    (define (new-cells color)
      (filter
        (lambda (p)
          (and (= (at g (first p) (second p)) 0)
               (= (at stage (first p) (second p)) color)))
        positions))
    (define ranked
      (sort colors
        (lambda (a b)
          (let ((na (length (new-cells a)))
                (nb (length (new-cells b))))
            (or (> na nb) (and (= na nb) (< a b)))))))
    (define winner (first ranked))
    (define won (new-cells winner))
    (define rs (map first won))
    (define cs (map second won))
    (define top (max 0 (- (apply min rs) 1)))
    (define bottom (min (- (rows g) 1) (+ (apply max rs) 1)))
    (define left (max 0 (- (apply min cs) 1)))
    (define right (min (- (cols g) 1) (+ (apply max cs) 1)))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (let ((v (at stage r c)))
          (if (not (= v 0))
              v
              (if (or (and (or (= r top) (= r bottom)) (<= left c) (<= c right))
                      (and (or (= c left) (= c right)) (<= top r) (<= r bottom)))
                  9
                  0)))))))
