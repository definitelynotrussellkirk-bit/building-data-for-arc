(rule!
 ;; Every mixed-color 8-connected object is a spacecraft.  Its majority color
 ;; is the hull and its minority cells are stored exhaust particles.  Infer the
 ;; geometric nose from the unique extreme hull tip aligned with the widest
 ;; cross-sections, erase the stored particles, and emit that many particles
 ;; from the nose.  Single-color objects remain unchanged.
 (lambda (g)
  (let ()
   (define h (rows g))
   (define w (cols g))
   (define dirs (list (list 'up -1 0 0) (list 'right 0 1 1)
                      (list 'down 1 0 2) (list 'left 0 -1 3)))
   (define (cell-color p) (at g (first p) (second p)))
   (define (color-count cells color)
    (length (filter (lambda (p) (= (cell-color p) color)) cells)))
   (define (candidate cells hull particles direction)
    (define name (first direction))
    (define dr (second direction))
    (define dc (third direction))
    (define order (fourth direction))
    (define projections (map (lambda (p) (+ (* (first p) dr) (* (second p) dc))) hull))
    (define extreme (apply max projections))
    (define tips
     (filter (lambda (p) (= (+ (* (first p) dr) (* (second p) dc)) extreme)) hull))
    (if (not (= (length tips) 1)) #f
     (let* ((tip (first tips))
            (keys (remove-duplicates
                   (map (lambda (p) (if (= dr 0) (second p) (first p))) cells)))
            (slices
             (map (lambda (key)
                   (filter (lambda (p) (= (if (= dr 0) (second p) (first p)) key)) cells)) keys))
            (widest (apply max (map length slices)))
            (wide (filter (lambda (slice) (= (length slice) widest)) slices))
            (centers
             (map (lambda (slice)
                   (/ (+ 0.0 (apply + (map (lambda (p) (if (= dr 0) (first p) (second p))) slice)))
                      (length slice))) wide))
            (center (/ (+ 0.0 (apply + centers)) (length centers)))
            (lateral-tip (if (= dr 0) (first tip) (second tip)))
            (alignment (abs (- lateral-tip center)))
            (depths
             (map (lambda (p) (- extreme (+ (* (first p) dr) (* (second p) dc)))) particles))
            (mean-depth (/ (+ 0.0 (apply + depths)) (length depths))))
      (list alignment (- mean-depth) order name dr dc tip))))
   (define (candidate<? a b)
    (cond ((< (first a) (first b)) #t)
          ((> (first a) (first b)) #f)
          ((< (second a) (second b)) #t)
          ((> (second a) (second b)) #f)
          (else (< (third a) (third b)))))
   (define (ship object)
    (define cells (obj-cells object))
    (define colors (sort (remove-duplicates (map cell-color cells)) <))
    (if (not (= (length colors) 2)) #f
     (let* ((a (first colors)) (b (second colors))
            (ca (color-count cells a)) (cb (color-count cells b))
            (hull-color (if (> ca cb) a b))
            (particle-color (if (> ca cb) b a)))
      (if (= ca cb) #f
       (let* ((hull (filter (lambda (p) (= (cell-color p) hull-color)) cells))
              (particles (filter (lambda (p) (= (cell-color p) particle-color)) cells))
              (candidates (filter identity (map (lambda (d) (candidate cells hull particles d)) dirs))))
        (if (null? candidates) #f
         (let ((chosen (first (sort candidates candidate<?))))
          (list particles particle-color (fifth chosen) (sixth chosen)
                (seventh chosen) (fourth chosen) hull-color cells))))))))
   ;; Stage A is the complete set of input-derived ship records: particle cells,
   ;; colors, geometric nose, heading and count.
   (define ships (filter identity (map ship (objects-multicolor g 0))))
   (define cleared
    (for/fold ((out g)) ((s ships))
     (for/fold ((acc out)) ((p (first s)))
      (set-cell acc (first p) (second p) 0))))
   (define extension 'particle_count)
   ;; Stage B consumes the records, selecting only the ray length policy.
   (for/fold ((out cleared)) ((s ships))
    (define particles (first s))
    (define color (second s))
    (define dr (third s))
    (define dc (fourth s))
    (define tip (fifth s))
    (define limit (if (equal? extension 'particle_count) (length particles) (+ h w)))
    (for/fold ((acc out)) ((k (range 1 (+ limit 1))))
     (define r (+ (first tip) (* k dr)))
     (define c (+ (second tip) (* k dc)))
     (if (and (<= 0 r) (< r h) (<= 0 c) (< c w))
         (set-cell acc r c color) acc))))))
