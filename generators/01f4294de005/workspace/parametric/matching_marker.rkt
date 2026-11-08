(rule!
  (let ((dummy 0))
    (let* ((palette (filter (lambda (v) (not (= v 0))) (first g)))
           (body (subgrid g 1 0 (- (rows g) 1) (- (cols g) 1)))
           (body-objects (objects body 0)))
      (for/fold ((out g)) ((obj (in-list body-objects)))
        (if (= (obj-color obj) 7)
            (let* ((color (list-ref palette (- (obj-size obj) 1)))
                   (marker
                    (first
                     (filter
                      (lambda (candidate)
                        (and (= (obj-color candidate) color)
                             (= (obj-size candidate) 1)))
                      body-objects)))
                   (anchor (first (obj-cells marker)))
                   (shape (normalize-cells (obj-cells obj)))
                   (original
                    (map (lambda (p) (list (+ 1 (first p)) (second p)))
                         (obj-cells obj)))
                   (echo
                    (map
                     (lambda (p)
                       (list (+ 1 (first anchor) (first p))
                             (+ (second anchor) (second p))))
                     shape)))
              (paint-cells (paint-cells out original color) echo color))
            out)))))
