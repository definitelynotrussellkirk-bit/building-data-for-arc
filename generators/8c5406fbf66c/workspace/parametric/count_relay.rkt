(rule!
  (let ((dummy 0))
    (define (active-anchors grid obj)
      (let ((color (obj-color obj)))
        (filter
          (lambda (p)
            (let ((r (first p)) (c (second p)))
              (and (< r (- (rows grid) 1))
                   (< c (- (cols grid) 1))
                   (= (at grid r c) color)
                   (= (at grid r (+ c 1)) color)
                   (= (at grid (+ r 1) c) color)
                   (= (at grid (+ r 1) (+ c 1)) color))))
          (obj-cells obj))))
    (define all-objects (objects g 0))
    (define source
      (first (filter (lambda (obj) (= (obj-color obj) 1)) all-objects)))
    (define candidates
      (sort
        (filter
          (lambda (obj) (member? (obj-color obj) (list 2 3 4 5 6 7)))
          all-objects)
        (lambda (a b) (< (obj-size a) (obj-size b)))))
    (define source-window-count (length (active-anchors g source)))
    (define target (list-ref candidates (- source-window-count 1)))
    (for/fold ((out g)) ((p (in-list (active-anchors g target))))
      (set-cell out (first p) (second p) 8))))
