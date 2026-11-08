(rule!
  ;; Counterfactual: after the canonical fill, choose the output color whose
 ;; raw key frame occupies the most input cells rather than using filled area.
 (lambda (g)
  (let ()
   (define dirs '((-1 0) (1 0) (0 -1) (0 1)))
   (define mask
    (grid-from-fn (rows g) (cols g)
     (lambda (r c) (if (= (at g r c) 0) 0 1))))
   (define groups (objects mask 0))
   (define tables
    (filter
     (lambda (o)
      (let ((colors (remove-duplicates
                     (map (lambda (p) (at g (first p) (second p))) (obj-cells o)))))
       (and (>= (length colors) 4)
            (= (obj-size o) (* (obj-h o) (obj-w o)))
            (or (= (obj-h o) 2) (= (obj-w o) 2)))))
     groups))
   (unless (= (length tables) 1)
    (error 'mapped-holes "expected one filled 2xN or Nx2 correspondence table"))
   (define table (first tables))
   (define table-cells (obj-cells table))
   (define outside-colors
    (remove-duplicates
     (for*/list ((r (range (rows g))) (c (range (cols g)))
                 #:when (and (not (= (at g r c) 0))
                             (not (member (list r c) table-cells))))
      (at g r c))))
   (define row-maps
    (if (= (obj-h table) 2)
     (let ((forward
            (for/list ((c (range (obj-c1 table) (+ (obj-c2 table) 1))))
             (list (at g (obj-r1 table) c) (at g (obj-r2 table) c)))))
       (list forward (map (lambda (p) (list (second p) (first p))) forward)))
     '()))
   (define col-maps
    (if (= (obj-w table) 2)
     (let ((forward
            (for/list ((r (range (obj-r1 table) (+ (obj-r2 table) 1))))
             (list (at g r (obj-c1 table)) (at g r (obj-c2 table))))))
       (list forward (map (lambda (p) (list (second p) (first p))) forward)))
     '()))
   (define candidates (append row-maps col-maps))
   (define (score mapping)
    (for/sum ((p mapping)) (if (member (first p) outside-colors) 1 0)))
   (define mapping
    (for/fold ((best (first candidates))) ((candidate (rest candidates)))
     (if (> (score candidate) (score best)) candidate best)))
   (define zero-mask
    (grid-from-fn (rows g) (cols g)
     (lambda (r c) (if (= (at g r c) 0) 1 0))))
   (define holes (objects zero-mask 0))
   (define (enclosed? o)
    (and (> (obj-r1 o) 0) (< (obj-r2 o) (- (rows g) 1))
         (> (obj-c1 o) 0) (< (obj-c2 o) (- (cols g) 1))))
   (define (border-colors o)
    (remove-duplicates
     (for*/list ((p (obj-cells o)) (d dirs)
                 #:when (let ((r (+ (first p) (first d)))
                              (c (+ (second p) (second d))))
                          (and (in-bounds? r c (rows g) (cols g))
                               (not (= (at g r c) 0)))))
      (at g (+ (first p) (first d)) (+ (second p) (second d))))))
   (define completed
    (for/fold ((out g)) ((hole holes))
     (let* ((border (if (enclosed? hole) (border-colors hole) '()))
            (entry (and (= (length border) 1) (assoc (first border) mapping))))
      (if entry
       (for/fold ((canvas out)) ((p (obj-cells hole)))
        (set-cell canvas (first p) (second p) (second entry)))
       out))))

   (define filled
    (for*/list ((r (range (rows g))) (c (range (cols g)))
                #:when (and (= (at g r c) 0) (not (= (at completed r c) 0))))
     (list r c (at completed r c))))
   (define keys (map first mapping))
   (define (raw-count key)
    (for*/sum ((r (range (rows g))) (c (range (cols g))))
     (if (and (= (at g r c) key) (not (member (list r c) table-cells))) 1 0)))
   (define raw-key
    (for/fold ((best (first keys))) ((key (rest keys)))
     (if (> (raw-count key) (raw-count best)) key best)))
   (define wrong-fill (second (assoc raw-key mapping)))
   (for/fold ((out completed)) ((p filled) #:when (= (third p) wrong-fill))
    (set-cell out (first p) (second p) 9))))))
