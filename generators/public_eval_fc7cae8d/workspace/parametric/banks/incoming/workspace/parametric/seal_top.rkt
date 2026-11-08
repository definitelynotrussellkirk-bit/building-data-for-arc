(rule!
  ;; Two distinct colored outer edges specify the target frame orientation.
  ;; Recover the isolated inner picture and its two matching guide edges.
  ;; Remove those guide edges, then apply the unique rotation/reflection
  ;; sending each inner guide edge to its matching outer edge.
  (let ()
    (define (edge x k)
      (cond [(= k 0) (first x)] [(= k 1) (map last x)]
            [(= k 2) (last x)] [else (map first x)]))
    (define (edge-index x color)
      (pick-max (range 4) (lambda (k) (count-if (lambda (v) (= v color)) (edge x k)))))
    (define (tx x k)
      (let loop ((out (if (>= k 4) (flip-lr x) x)) (n (modulo k 4)))
        (if (= n 0) out (loop (rotate-cw out) (- n 1)))))
    (define (seal x)
      (define fill (mode x 0))
      (for/fold ((out x)) ((o (in-list (objects x -1)))
                            #:when (and (= (obj-color o) 0) (= (obj-r1 o) 0)))
        (paint-cells out (obj-cells o) fill)))
    (define guides
      (filter (lambda (color)
        (and (not (= color 5))
             (for/or ((k (in-range 4)))
               (> (* 2 (count-if (lambda (v) (= v color)) (edge g k)))
                  (length (edge g k)))))) (range 1 10)))
    (define inner
      (pick-max
        (filter (lambda (o)
          (and (> (obj-r1 o) 0) (> (obj-c1 o) 0)
               (< (obj-r2 o) (- (rows g) 1)) (< (obj-c2 o) (- (cols g) 1))))
          (objects-multicolor g 0)) obj-size))
    (define frame (subgrid g (obj-r1 inner) (obj-c1 inner) (obj-r2 inner) (obj-c2 inner)))
    (define source-edges (map (lambda (c) (edge-index frame c)) guides))
    (define code
      (for/first ((k (in-range 8))
          #:when (for/and ((color (in-list guides)))
                   (= (edge-index (tx frame k) color) (edge-index g color)))) k))
    (define payload
      (subgrid frame
        (if (member 0 source-edges) 1 0) (if (member 3 source-edges) 1 0)
        (- (rows frame) (if (member 2 source-edges) 2 1))
        (- (cols frame) (if (member 1 source-edges) 2 1))))
    (define oriented (tx payload code))
    ;; RESULT
    (seal oriented)))
