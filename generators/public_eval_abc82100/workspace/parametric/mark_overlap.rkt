(rule!
  ;; Cyan shapes are stencils. A two-cell handle specifies outer source color
  ;; and inner paint color; its continuation onto the stencil bbox is the anchor.
  ;; Replace all remaining source markers simultaneously with translated stencils,
  ;; clipping at the canvas boundary. Remove templates/handles; keep unmapped dots.
  ;; When adjacent thin templates touch, split their cyan region by the maximal
  ;; straight cyan runs reached from their distinct handles.
  (let ()
    (define (plus p d n) (list (+ (first p) (* n (first d))) (+ (second p) (* n (second d)))))
    (define (value p) (safe-at g (first p) (second p) 0))
    (define (valid-key? a d)
      (define s (value (plus a d -2)))
      (define t (value (plus a d -1)))
      (and (> s 0) (> t 0) (not (= s 8)) (not (= t 8)) (not (= s t))))
    ;; Template = source color, paint color, source cell, paint cell, anchor, cyan cells.
    (define (template a d cells)
      (list (value (plus a d -2)) (value (plus a d -1))
            (plus a d -2) (plus a d -1) a cells))
    (define (candidates o)
      (define cells (obj-cells o))
      (define normal
        (append-map
          (lambda (d)
            (define anchors
              (if (= (first d) 0)
                (for/list ((r (in-range (obj-r1 o) (+ (obj-r2 o) 1))))
                  (list r (if (= (second d) 1) (obj-c1 o) (obj-c2 o))))
                (for/list ((c (in-range (obj-c1 o) (+ (obj-c2 o) 1))))
                  (list (if (= (first d) 1) (obj-r1 o) (obj-r2 o)) c))))
            (for/list ((a (in-list anchors)) #:when (valid-key? a d)) (template a d cells)))
          cardinal-deltas))
      (if (not (null? normal)) normal
        (for*/list ((a (in-list cells)) (d (in-list cardinal-deltas)) #:when (valid-key? a d))
          (template a d
            (let loop ((p a) (acc '()))
              (if (member p cells) (loop (plus p d 1) (cons p acc)) (reverse acc)))))))
    (define templates
      (append-map candidates (filter (lambda (o) (= (obj-color o) 8)) (objects-8 g 0))))
    (define erased
      (append (find-color g 8) (append-map (lambda (t) (list (third t) (fourth t))) templates)))
    (define sources (map first templates))
    (define (offsets t)
      (define a (list-ref t 4))
      (map (lambda (p) (list (- (first p) (first a)) (- (second p) (second a)))) (list-ref t 5)))
    (define instances
      (append-map (lambda (t)
        (for/list ((p (in-list (grid-positions g)))
                   #:when (and (= (value p) (first t)) (not (member p erased))))
          (list (second t)
            (filter (lambda (q) (in-bounds? (first q) (second q) (rows g) (cols g)))
              (map (lambda (d) (plus p d 1)) (offsets t)))))) templates))
    (define clean
      (cellmap g (r c v) (if (or (member (list r c) erased) (member v sources)) 0 v)))
    (define painted
      (for/fold ((out clean)) ((instance (in-list instances)))
        (paint-cells out (second instance) (first instance))))
    (define footprints (append-map second instances))
    ;; RESULT
    (cellmap painted (r c v) (if (>= (count-if (lambda (p) (equal? p (list r c))) footprints) 2) 9 v))))
