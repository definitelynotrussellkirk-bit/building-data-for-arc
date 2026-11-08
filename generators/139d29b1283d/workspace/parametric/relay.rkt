(rule!
  (let ((dummy 0))
    (define (norm-cells cells) (sort (normalize-cells cells) cell<))
    (define (objs-color grid color)
      (filter (lambda (obj) (= (obj-color obj) color)) (objects grid 0)))
    (define (first-pos grid color) (first (find-color grid color)))
    (let* ((template
            (first
             (sort (objs-color g 3)
                   (lambda (a b) (> (obj-size a) (obj-size b))))))
           (shape (norm-cells (obj-cells template)))
           (a1 (first-pos g 1))
           (a2 (first-pos g 2))
           (stamp1
            (map (lambda (p)
                   (list (+ (first a1) (first p))
                         (+ (second a1) (second p))))
                 shape))
           (stamp2
            (map (lambda (p)
                   (list (+ (first a2) (first p))
                         (+ (second a2) (second p))))
                 shape))
           (overlap
            (filter (lambda (p)
                      (and (member? p stamp2)
                           (in-bounds? (first p) (second p) (rows g) (cols g))))
                    stamp1))
           (payloads (objs-color g 4))
           (payload
            (first
             (filter (lambda (obj) (= (obj-size obj) (length overlap)))
                     payloads)))
           (stage-a (paint-cells (empty-grid (rows g) (cols g) 0) overlap 8)))
      (paint-cells stage-a (obj-cells payload) 8))))
