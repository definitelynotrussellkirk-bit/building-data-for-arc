(rule!
 (lambda (g)
   (let ()
     (define contour-mode 0) ; 0 = fill enclosed holes for the outer contour
     (define h (rows g))
     (define w (cols g))
     (define seed (first (find-color g 6)))
     (define traversable
       (grid-from-fn h w
         (lambda (r c) (if (or (= (at g r c) 8) (= (at g r c) 6)) 0 1))))
     (define region
       (first (filter (lambda (cells) (member? seed cells))
                      (find-0-regions traversable 0))))
     (define complement-mask
       (grid-from-fn h w
         (lambda (r c) (if (member? (list r c) region) 1 0))))
     (define complement (find-0-regions complement-mask 0))
     (define (border? p)
       (or (= (first p) 0) (= (second p) 0)
           (= (first p) (- h 1)) (= (second p) (- w 1))))
     (define holes
       (filter (lambda (cells) (not (any? border? cells))) complement))
     (define hole-cells (if (null? holes) '() (apply append holes)))
     (define wall-mask
       (grid-from-fn h w (lambda (r c) (if (= (at g r c) 1) 0 1))))
     (define wall-components (find-0-regions wall-mask 0))
     (define (touches-region? cells)
       (any?
        (lambda (p)
          (let ((r (first p)) (c (second p)))
            (or (member? (list (- r 1) c) region)
                (member? (list (+ r 1) c) region)
                (member? (list r (- c 1)) region)
                (member? (list r (+ c 1)) region))))
        cells))
     (define kept-walls
       (let ((xs (filter touches-region? wall-components)))
         (if (null? xs) '() (apply append xs))))
     (define domain (if (= contour-mode 0) (append region hole-cells) region))
     (define (boundary? r c)
       (for*/or ((dr (in-range -1 2)) (dc (in-range -1 2))
                 #:unless (and (= dr 0) (= dc 0)))
         (let ((nr (+ r dr)) (nc (+ c dc)))
           (or (< nr 0) (>= nr h) (< nc 0) (>= nc w)
               (not (member? (list nr nc) domain))))))
     (grid-from-fn h w
       (lambda (r c)
         (let ((p (list r c)))
           (cond
             ((member? p region)
              (if (= (at g r c) 6) 6 (if (boundary? r c) 7 8)))
             ((or (member? p hole-cells) (member? p kept-walls)) (at g r c))
             (else 8))))))))
