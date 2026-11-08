#lang racket
;; Heightmap / 3D Lattice operations for ARC grids
;;
;; Model: A 2D grid is the TOP-DOWN VIEW of a 3D heightmap.
;; Color value = z-height. Cell value 5 means solid blocks at z=0..4.
;; The 3D lattice is a boolean array: lattice[x][y][z] = occupied?
;;
;; Operations:
;;   grid->lattice  : 2D heightmap → 3D boolean lattice
;;   lattice->grid  : 3D lattice → 2D heightmap (top-down projection)
;;   roll-forward/back/left/right : rotate the 3D object
;;   project-front/side/back      : view from different faces
;;   gravity-3d     : blocks fall in current "down" direction
;;
;; The lattice is represented as a hash: (x . (y . z)) → #t
;; with metadata for bounds: (list x-max y-max z-max)

(provide (all-defined-out))

;; ============================================================
;; Lattice representation
;; ============================================================

;; A lattice is (hasheq 'cells <hash of (x y z) → #t>
;;                      'xmax N  'ymax N  'zmax N)

(define (make-lattice cells xmax ymax zmax)
  (hasheq 'cells cells 'xmax xmax 'ymax ymax 'zmax zmax))

(define (lattice-cells lat) (hash-ref lat 'cells))
(define (lattice-xmax lat) (hash-ref lat 'xmax))
(define (lattice-ymax lat) (hash-ref lat 'ymax))
(define (lattice-zmax lat) (hash-ref lat 'zmax))

(define (lattice-has? lat x y z)
  (hash-has-key? (lattice-cells lat) (list x y z)))

(define (lattice-set lat x y z)
  (make-lattice
    (hash-set (lattice-cells lat) (list x y z) #t)
    (max x (lattice-xmax lat))
    (max y (lattice-ymax lat))
    (max z (lattice-zmax lat))))

;; ============================================================
;; Grid ↔ Lattice conversion
;; ============================================================

(define (grid->lattice g)
  ;; Heightmap interpretation: cell value h → blocks at z=0..h-1
  (define h (length g))
  (define w (if (empty? g) 0 (length (first g))))
  (define cells (make-hash))
  (define zmax 0)
  (for* ([r (in-range h)] [c (in-range w)])
    (define val (list-ref (list-ref g r) c))
    (when (> val 0)
      (set! zmax (max zmax val))
      (for ([z (in-range val)])
        (hash-set! cells (list r c z) #t))))
  (make-lattice cells (sub1 h) (sub1 w) (sub1 (max 1 zmax))))

(define (lattice->grid lat)
  ;; Top-down projection: for each (x,y), find max z+1 where block exists
  (define xmax (lattice-xmax lat))
  (define ymax (lattice-ymax lat))
  (define zmax (lattice-zmax lat))
  (define cells (lattice-cells lat))
  (for/list ([x (in-range (add1 xmax))])
    (for/list ([y (in-range (add1 ymax))])
      ;; Find highest occupied z
      (define top-z
        (for/fold ([best 0]) ([z (in-range (add1 zmax))])
          (if (hash-has-key? cells (list x y z)) (add1 z) best)))
      top-z)))

;; ============================================================
;; Projections (views from different faces)
;; ============================================================

(define (project-front lat)
  ;; View along y-axis (from y=0 looking toward y=max)
  ;; Result grid: rows=z (top to bottom), cols=x
  ;; For each (x,z): is there ANY y with a block?
  (define xmax (lattice-xmax lat))
  (define zmax (lattice-zmax lat))
  (define ymax (lattice-ymax lat))
  (define cells (lattice-cells lat))
  (for/list ([z (in-range zmax -1 -1)])  ;; top z first (row 0 = highest)
    (for/list ([x (in-range (add1 xmax))])
      (if (for/or ([y (in-range (add1 ymax))])
            (hash-has-key? cells (list x y z)))
          (add1 z) 0))))  ;; color = height level

(define (project-side lat)
  ;; View along x-axis (from x=0 looking toward x=max)
  ;; Result grid: rows=z (top to bottom), cols=y
  (define xmax (lattice-xmax lat))
  (define ymax (lattice-ymax lat))
  (define zmax (lattice-zmax lat))
  (define cells (lattice-cells lat))
  (for/list ([z (in-range zmax -1 -1)])
    (for/list ([y (in-range (add1 ymax))])
      (if (for/or ([x (in-range (add1 xmax))])
            (hash-has-key? cells (list x y z)))
          (add1 z) 0))))

(define (project-back lat)
  ;; View along y-axis from y=max looking toward y=0
  ;; Same as project-front but mirrored
  (map reverse (project-front lat)))

;; ============================================================
;; 3D Rotations (roll the object)
;; ============================================================

(define (transform-lattice lat transform-fn new-bounds-fn)
  ;; Apply a coordinate transform to all cells
  (define cells (lattice-cells lat))
  (define new-cells (make-hash))
  (define bounds (new-bounds-fn (lattice-xmax lat) (lattice-ymax lat) (lattice-zmax lat)))
  (for ([(key _) (in-hash cells)])
    (define new-key (transform-fn (first key) (second key) (third key)))
    (hash-set! new-cells new-key #t))
  (make-lattice new-cells (first bounds) (second bounds) (third bounds)))

(define (roll-forward lat)
  ;; Tip the object toward you: rotate around x-axis
  ;; (x, y, z) → (x, z, ymax-y)
  (define ymax (lattice-ymax lat))
  (transform-lattice lat
    (lambda (x y z) (list x z (- ymax y)))
    (lambda (xm ym zm) (list xm zm ym))))

(define (roll-back lat)
  ;; Tip away: rotate around x-axis (opposite direction)
  ;; (x, y, z) → (x, zmax-z, y)
  (define zmax (lattice-zmax lat))
  (transform-lattice lat
    (lambda (x y z) (list x (- zmax z) y))
    (lambda (xm ym zm) (list xm zm ym))))

(define (roll-left lat)
  ;; Tip left: rotate around y-axis
  ;; (x, y, z) → (z, y, xmax-x)
  (define xmax (lattice-xmax lat))
  (transform-lattice lat
    (lambda (x y z) (list z y (- xmax x)))
    (lambda (xm ym zm) (list zm ym xm))))

(define (roll-right lat)
  ;; Tip right: rotate around y-axis (opposite)
  ;; (x, y, z) → (zmax-z, y, x)
  (define zmax (lattice-zmax lat))
  (transform-lattice lat
    (lambda (x y z) (list (- zmax z) y x))
    (lambda (xm ym zm) (list zm ym xm))))

(define (spin-cw lat)
  ;; Rotate around z-axis (top view rotation)
  ;; (x, y, z) → (y, xmax-x, z)
  (define xmax (lattice-xmax lat))
  (transform-lattice lat
    (lambda (x y z) (list y (- xmax x) z))
    (lambda (xm ym zm) (list ym xm zm))))

(define (spin-ccw lat)
  ;; Rotate around z-axis counterclockwise
  ;; (x, y, z) → (ymax-y, x, z)
  (define ymax (lattice-ymax lat))
  (transform-lattice lat
    (lambda (x y z) (list (- ymax y) x z))
    (lambda (xm ym zm) (list ym xm zm))))

;; ============================================================
;; Gravity: blocks fall to lowest available z
;; ============================================================

(define (gravity-3d lat)
  ;; For each (x,y) column, compact blocks downward
  (define xmax (lattice-xmax lat))
  (define ymax (lattice-ymax lat))
  (define zmax (lattice-zmax lat))
  (define cells (lattice-cells lat))
  (define new-cells (make-hash))
  (define new-zmax 0)
  (for* ([x (in-range (add1 xmax))]
         [y (in-range (add1 ymax))])
    ;; Count blocks in this column
    (define count
      (for/sum ([z (in-range (add1 zmax))])
        (if (hash-has-key? cells (list x y z)) 1 0)))
    ;; Place them at z=0..count-1
    (for ([z (in-range count)])
      (hash-set! new-cells (list x y z) #t))
    (set! new-zmax (max new-zmax (sub1 (max 1 count)))))
  (make-lattice new-cells xmax ymax new-zmax))

;; ============================================================
;; Convenience: grid-level operations via 3D
;; ============================================================

(define (grid-roll-forward g)
  ;; Roll the heightmap forward and return new top-down view
  (lattice->grid (gravity-3d (roll-forward (grid->lattice g)))))

(define (grid-roll-back g)
  (lattice->grid (gravity-3d (roll-back (grid->lattice g)))))

(define (grid-roll-left g)
  (lattice->grid (gravity-3d (roll-left (grid->lattice g)))))

(define (grid-roll-right g)
  (lattice->grid (gravity-3d (roll-right (grid->lattice g)))))

(define (grid-front-view g)
  ;; What you see looking at the grid from the front
  (project-front (grid->lattice g)))

(define (grid-side-view g)
  (project-side (grid->lattice g)))

;; ============================================================
;; Slice operations
;; ============================================================

(define (slice-at-height lat z)
  ;; Cross-section at height z: returns 2D grid (1 = block, 0 = empty)
  (define xmax (lattice-xmax lat))
  (define ymax (lattice-ymax lat))
  (define cells (lattice-cells lat))
  (for/list ([x (in-range (add1 xmax))])
    (for/list ([y (in-range (add1 ymax))])
      (if (hash-has-key? cells (list x y z)) 1 0))))

(define (grid-slice g z)
  ;; Which cells have height > z?
  (define h (length g))
  (define w (if (empty? g) 0 (length (first g))))
  (for/list ([r (in-range h)])
    (for/list ([c (in-range w)])
      (if (> (list-ref (list-ref g r) c) z) 1 0))))

;; ============================================================
;; Multi-color lattice (each color = different material at z=color)
;; ============================================================

(define (grid->color-lattice g)
  ;; Instead of heightmap, each cell places ONE block at z=color_value
  ;; Color 0 = empty, color 3 = block at z=3
  (define h (length g))
  (define w (if (empty? g) 0 (length (first g))))
  (define cells (make-hash))
  (define zmax 0)
  (for* ([r (in-range h)] [c (in-range w)])
    (define val (list-ref (list-ref g r) c))
    (when (> val 0)
      (set! zmax (max zmax val))
      (hash-set! cells (list r c val) #t)))
  (make-lattice cells (sub1 h) (sub1 w) zmax))

(define (color-lattice->grid lat)
  ;; Top-down: show the highest color at each (x,y)
  (define xmax (lattice-xmax lat))
  (define ymax (lattice-ymax lat))
  (define zmax (lattice-zmax lat))
  (define cells (lattice-cells lat))
  (for/list ([x (in-range (add1 xmax))])
    (for/list ([y (in-range (add1 ymax))])
      (for/fold ([best 0]) ([z (in-range (add1 zmax))])
        (if (hash-has-key? cells (list x y z)) z best)))))
