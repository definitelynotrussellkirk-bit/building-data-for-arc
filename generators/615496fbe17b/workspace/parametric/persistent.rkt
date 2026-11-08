(rule!
  (let ((dummy 0))
    (define square-offsets
      (for*/list ((dr (in-range -1 2)) (dc (in-range -1 2))) (list dr dc)))
    (define (grow-from-centers grid centers offsets)
      (remove-duplicates
       (filter
        (lambda (p) (in-bounds? (first p) (second p) (rows grid) (cols grid)))
        (flatmap
         (lambda (p)
           (map (lambda (d)
                  (list (+ (first p) (first d)) (+ (second p) (second d))))
                offsets))
         centers))))
    (define (crop-cells cells (color 8))
      (let* ((bb (bbox-of-cells cells))
             (r1 (first bb)) (c1 (second bb))
             (r2 (third bb)) (c2 (fourth bb))
             (norm (map (lambda (p) (list (- (first p) r1) (- (second p) c1))) cells)))
        (paint-cells (empty-grid (+ 1 (- r2 r1)) (+ 1 (- c2 c1)) 0) norm color)))
    (define (obj< a b)
      (let ((ba (obj-bbox a)) (bb (obj-bbox b)))
        (if (= (first ba) (first bb))
            (< (second ba) (second bb))
            (< (first ba) (first bb)))))
    (define (holes-in-cells cells)
      (let* ((sub (crop-cells cells 2))
             (regions (find-0-regions sub 0)))
        (count-where
         (lambda (region)
           (not
            (any?
             (lambda (p)
               (or (= (first p) 0) (= (second p) 0)
                   (= (first p) (- (rows sub) 1))
                   (= (second p) (- (cols sub) 1))))
             region)))
         regions)))
    (let* ((objs (sort (objects g 0) obj<))
           (chosen
            (first
             (filter
              (lambda (obj)
                (let* ((before (holes-in-cells (obj-cells obj)))
                       (after
                        (holes-in-cells
                         (grow-from-centers g (obj-cells obj) square-offsets))))
                  (and (> before 0) (= before after))))
              objs))))
      (crop-cells (obj-cells chosen) 8))))
