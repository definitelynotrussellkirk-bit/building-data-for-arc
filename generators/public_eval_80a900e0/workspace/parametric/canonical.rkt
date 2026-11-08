(rule!
 (lambda (g)
  (define solid? #f)
  (define (xy u v) (list (/ (+ u v) 2) (/ (- u v) 2)))
  (define (inside? p)
   (and (<= 0 (first p)) (< (first p) (rows g))
        (<= 0 (second p)) (< (second p) (cols g))))
  (define (frame-data obj)
   (let* ([cells (obj-cells obj)]
          [us (map (lambda (p) (+ (first p) (second p))) cells)]
          [vs (map (lambda (p) (- (first p) (second p))) cells)]
          [u0 (apply min us)] [u1 (apply max us)]
          [v0 (apply min vs)] [v1 (apply max vs)]
          [border (for*/list ([u (in-range u0 (+ u1 1) 2)]
                              [v (in-range v0 (+ v1 1) 2)]
                              #:when (or (= u u0) (= u u1) (= v v0) (= v v1)))
                    (xy u v))])
    (and (>= (- u1 u0) 4) (>= (- v1 v0) 4)
         (= (length cells) (length border))
         (all? (lambda (p) (member? p cells)) border)
         (list (obj-color obj) u0 v0 u1 v1))))
  (define frames
   (filter (lambda (x) x)
    (map frame-data (filter (lambda (o) (> (obj-color o) 1)) (objects-8 g 0)))))
  (define (faces frame)
   (let ([u0 (second frame)] [v0 (third frame)]
         [u1 (fourth frame)] [v1 (fifth frame)])
    (list
     (list (list -1 -1) (for/list ([v (in-range v0 (+ v1 1) 2)]) (xy (- u0 2) v)))
     (list (list 1 1) (for/list ([v (in-range v0 (+ v1 1) 2)]) (xy (+ u1 2) v)))
     (list (list -1 1) (for/list ([u (in-range u0 (+ u1 1) 2)]) (xy u (- v0 2))))
     (list (list 1 -1) (for/list ([u (in-range u0 (+ u1 1) 2)]) (xy u (+ v1 2)))))))
  (define caps
   (apply append
    (map (lambda (frame)
      (filter (lambda (x) x)
       (map (lambda (face)
         (let* ([points (second face)] [visible (filter inside? points)]
                [colors (remove-duplicates (map (lambda (p) (at g (first p) (second p))) visible))])
          (and (= (length colors) 1) (> (first colors) 1)
               (not (= (first colors) (first frame)))
               (list (first colors) (first face) points))))
        (faces frame)))) frames)))
  (define ray-specs caps)
  (for/fold ([out g]) ([cap ray-specs])
   (let* ([color (first cap)] [direction (second cap)] [points (third cap)]
          [origins (if solid? points (list (first points) (last points)))]
          [targets (apply append
            (map (lambda (origin)
              (filter (lambda (p) (and (inside? p) (= (at g (first p) (second p)) 1)))
               (for/list ([n (in-range 1 (+ (rows g) (cols g)))])
                (list (+ (first origin) (* n (first direction)))
                      (+ (second origin) (* n (second direction))))))) origins))])
    (paint-cells out targets color)))))
