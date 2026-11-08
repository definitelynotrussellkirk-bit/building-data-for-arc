(rule!
 (lambda (g)
  (let* ((h (rows g))
         (w (cols g))
         (cover (at g (- h 1) (- w 1)))
         (top-h
          (let loop ((r 0))
           (if (or (>= r h) (= (at g r 0) cover)) r (loop (+ r 1)))))
         (prefix
          (let loop ((c 0) (acc (list)))
           (if (or (>= c w) (= (at g 0 c) cover))
               acc
               (loop (+ c 1) (append acc (list (at g 0 c)))))))
         (n (length prefix))
         (col-period
          (find-first
           (lambda (p)
            (for/and ((i (range 0 n)))
             (= (nth prefix i) (nth prefix (modulo i p)))))
           (range 1 (+ n 1))))
         (row-period
          (find-first
           (lambda (p)
            (for/and ((r (range 0 top-h)))
             (for/and ((c (range 0 col-period)))
              (= (at g r c) (at g (modulo r p) c)))))
           (range 1 (+ top-h 1))))
         (stage-a
          (cellmap g (r c v)
           (at g (modulo r row-period) (modulo (+ c 1) col-period))))
         (spanning
          (find-first
           (lambda (obj)
            (let ((bb (bbox-of-cells (obj-cells obj))))
             (and (= (first bb) 0)
                  (= (second bb) 0)
                  (= (third bb) (- h 1))
                  (= (fourth bb) (- w 1)))))
           (objects stage-a 0))))
    (paint-cells stage-a (obj-cells spanning) cover))))
