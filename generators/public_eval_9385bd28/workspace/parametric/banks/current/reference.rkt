(rule!
 (lambda (g)
  (let ()
   (define finish 'combine)
   (define h (rows g))
   (define w (cols g))
   (define bg (mode g -1))
   (define (inside-box? p box)
    (and (<= (first box) (first p) (third box))
         (<= (second box) (second p) (fourth box))))
   (define (box-area box)
    (* (+ 1 (- (third box) (first box)))
       (+ 1 (- (fourth box) (second box)))))
   (define (mask-of cells)
    (paint-cells (empty-grid h w 0) cells 1))
   ;; Detect multicolor 4-connected groups by applying the ordinary object
   ;; finder to a binary non-background mask.
   (define foreground-mask
    (grid-from-fn h w (lambda (r c) (if (= (at g r c) bg) 0 1))))
   (define groups (objects foreground-mask 0))
   (define candidates
    (filter
     (lambda (obj)
      (let* ((cells (obj-cells obj))
             (box (bbox-of-cells cells))
             (r0 (first box)) (c0 (second box))
             (r1 (third box)) (c1 (fourth box))
             (colors (remove-duplicates
                      (map (lambda (p) (at g (first p) (second p))) cells))))
       (and (= (- c1 c0) 1)
            (>= (+ 1 (- r1 r0)) 2)
            (>= (length colors) 2)
            (andmap (lambda (r) (not (= (at g r c0) bg)))
                    (range r0 (+ r1 1))))))
     groups))
   (when (not (= (length candidates) 1))
    (error 'keyed-compose "expected exactly one two-column multicolor key"))
   (define key (first candidates))
   (define key-box (bbox-of-cells (obj-cells key)))
   (define kr0 (first key-box))
   (define kc0 (second key-box))
   (define kr1 (third key-box))
   (define key-cells
    (positions-in-rect (first key-box) (second key-box)
                       (third key-box) (fourth key-box)))
   ;; Entry shape: (source target key-row scene-cells source-components bbox).
   (define entries
    (for/list ((r (in-range kr0 (+ kr1 1))))
     (let* ((source (at g r kc0))
            (target (at g r (+ kc0 1)))
            (scene (filter (lambda (p) (not (member p key-cells)))
                           (find-color g source)))
            (comps (if (empty? scene) '() (objects (mask-of scene) 0)))
            (box (bbox-of-cells scene)))
      (list source target r scene comps box))))
   (define (entry-source e) (first e))
   (define (entry-target e) (second e))
   (define (entry-row e) (third e))
   (define (entry-cells e) (fourth e))
   (define (entry-components e) (fifth e))
   (define (entry-box e) (sixth e))
   (define (transparent? e)
    (or (= (entry-target e) 0) (= (entry-target e) bg)))
   (define (apply-entry e out)
    (if (empty? (entry-cells e))
        out
        (let* ((box (entry-box e))
               (rect (positions-in-rect (first box) (second box)
                                        (third box) (fourth box)))
               (painted
                (if (transparent? e)
                    (paint-cells out
                     (map (lambda (p)
                           (list (first p) (second p)
                                 (at g (first p) (second p))))
                          rect))
                    (recolor-cells out rect (entry-target e)))))
         (if (and (not (transparent? e))
                  (>= (length (entry-components e)) 2))
             (recolor-cells painted (entry-cells e) (entry-source e))
             painted))))
   ;; The lower key row is the bottom layer and the upper key row the top layer.
   (define composed (foldl apply-entry g (reverse entries)))
   (define changed
    (filter
     (lambda (p)
      (and (not (member p key-cells))
           (not (= (at composed (first p) (second p))
                   (at g (first p) (second p))))))
     (grid-positions g)))
   (cond
    ((eq? finish 'combine) composed)
    ((eq? finish 'largest-change)
     (if (empty? changed)
         composed
         (let* ((changed-objects (objects (mask-of changed) 0))
                (selected (pick-max changed-objects obj-size)))
          (recolor-cells composed (obj-cells selected) 9))))
    ((eq? finish 'raw-box)
     (let* ((visible-entries
             (filter (lambda (e)
                      (and (not (empty? (entry-cells e)))
                           (not (transparent? e))))
                     entries))
            (raw (pick-max visible-entries
                           (lambda (e) (box-area (entry-box e)))))
            (selected
             (if raw
                 (filter (lambda (p) (inside-box? p (entry-box raw))) changed)
                 '())))
      (recolor-cells composed selected 9)))
    (else (error 'keyed-compose "unknown finish mode"))))))
