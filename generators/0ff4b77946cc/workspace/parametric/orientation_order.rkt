(rule!
  (let* ((raw-objs (objects g 0))
         (largest
          (first
           (sort raw-objs
                 (lambda (a b)
                   (cond [(not (= (obj-size a) (obj-size b))) (> (obj-size a) (obj-size b))]
                         [(not (= (obj-h a) (obj-h b))) (< (obj-h a) (obj-h b))]
                         [(not (= (obj-w a) (obj-w b))) (< (obj-w a) (obj-w b))]
                         [else (< (obj-color a) (obj-color b))])))))
         (ascending? (> (obj-h largest) (obj-w largest)))
         (objs
          (sort raw-objs
                (lambda (a b)
                  (cond [(not (= (obj-size a) (obj-size b)))
                         (if ascending? (< (obj-size a) (obj-size b)) (> (obj-size a) (obj-size b)))]
                        [(not (= (obj-h a) (obj-h b))) (< (obj-h a) (obj-h b))]
                        [(not (= (obj-w a) (obj-w b))) (< (obj-w a) (obj-w b))]
                        [else (< (obj-color a) (obj-color b))])))))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (let loop ([remaining objs] [offset 0])
          (cond [(empty? remaining) 0]
                [(and (>= c offset) (< c (+ offset (obj-w (first remaining)))))
                 (let* ((obj (first remaining))
                        (rr (+ (obj-r1 obj) r))
                        (cc (+ (obj-c1 obj) (- c offset))))
                   (if (and (< r (obj-h obj))
                            (member? (list rr cc) (obj-cells obj)))
                       (at g rr cc)
                       0))]
                [else
                 (loop (rest remaining)
                       (+ offset (obj-w (first remaining)) 1))]))))))
