(rule!
 (let ((dummy 0))
  (define (list< a b)
   (cond ((empty? a) #f)
         ((< (first a) (first b)) #t)
         ((> (first a) (first b)) #f)
         (else (list< (rest a) (rest b)))))
  (define headers (filter (lambda (v) (not (= v 0))) (first g)))
  (define objs
   (sort
    (filter (lambda (obj) (= (obj-color obj) 8)) (objects g 0))
    (lambda (a b)
     (or (< (obj-size a) (obj-size b))
         (and (= (obj-size a) (obj-size b))
              (list< (obj-bbox a) (obj-bbox b)))))))
  (define ranked
   (let loop ((rest-objs objs) (rest-headers headers) (out g))
    (if (or (empty? rest-objs) (empty? rest-headers))
        out
        (loop (rest rest-objs)
              (rest rest-headers)
              (paint-cells out (obj-cells (first rest-objs)) (first rest-headers))))))
  (define h (rows g))
  (define w (cols g))
  (define marker
   (first
    (for*/list ((r (range 2 h))
                (c (range w))
                #:when (= (at g r c) 9))
     (list r c))))
  (define mr (first marker))
  (define mc (second marker))
  (define hit
   (let loop ((c (+ mc 1)))
    (if (>= c w)
        #f
        (let ((v (at ranked mr c)))
         (if (!= v 0) (list c v) (loop (+ c 1)))))))
  (define relay-color (second hit))
  (define swatch-col
   (find-first (lambda (c) (= (at g (- h 1) c) relay-color)) (range w)))
  (build-grid h w (r c)
   (if (and (>= r 2) (= c swatch-col)) 9 (at ranked r c)))))
