(rule!
 ;; Edge-anchored straight poles hold bent monochrome 8-connected strands.
 ;; A strand starts beside the pole's inner endpoint. Its forward obstacle is
 ;; the nearest feasible non-role component, on the same transverse side.
 ;; Measure the strand's cell count and derive the obstacle's per-slice outer
 ;; contour. Approach that contour at unit diagonal speed, follow its surface,
 ;; then turn inward diagonally after its last slice. Stop at the measured
 ;; number of cells or the first canvas boundary. Other components are retained.
 (lambda (g)
  (let ()
   (define extra-length 0)
   (define contour-mode 'exact)
   (define bg (mode g -1))
   (define objs (objects-8 g bg))
   (define (coord p axis) (list-ref p axis))
   (define (point primary transverse axis)
     (if (= axis 0) (list primary transverse) (list transverse primary)))
   (define (extent cells axis smallest)
     (apply (if smallest min max) (map (lambda (p) (coord p axis)) cells)))
   ;; Role record: pole index, strand index, axis, direction, side, anchor.
   (define roles
     (apply append
      (for/list ([i (range (length objs))])
       (define o (list-ref objs i))
       (define cells (obj-cells o))
       (if (< (length cells) 2) '()
        (apply append
         (for/list ([axis '(0 1)])
          (define bound (if (= axis 0) h w))
          (define lo (extent cells axis #t))
          (define hi (extent cells axis #f))
          (define cross (- 1 axis))
          (if (or (not (= (extent cells cross #t) (extent cells cross #f)))
                  (and (not (= lo 0)) (not (= hi (- bound 1))))
                  (and (= lo 0) (= hi (- bound 1)))) '()
           (let* ([direction (if (= lo 0) 1 -1)]
                  [tip (if (= direction 1) hi lo)]
                  [base (extent cells cross #t)])
            (apply append
             (for/list ([side '(-1 1)])
              (define anchor (point tip (+ base side) axis))
              (define j (for/first ([k (range (length objs))]
                                   #:when (and (not (= k i)) (member anchor (obj-cells (list-ref objs k))))) k))
              (if (and j (andmap (lambda (p) (<= (* direction (- (coord p axis) tip)) 0))
                                (obj-cells (list-ref objs j))))
                  (list (list i j axis direction side anchor)) '())))))))))))
   (define used (apply append (map (lambda (role) (list (first role) (second role))) roles)))
   ;; Add a derived obstacle contour to each legal role record.
   (define records
    (filter (lambda (x) x)
     (for/list ([role roles])
      (define axis (list-ref role 2))
      (define direction (list-ref role 3))
      (define side (list-ref role 4))
      (define anchor (list-ref role 5))
      (define (forward p) (* direction (- (coord p axis) (coord anchor axis))))
      (define choices
       (filter (lambda (x) x)
        (for/list ([j (range (length objs))] #:unless (member j used))
         (define cells (obj-cells (list-ref objs j)))
         (define us (sort (remove-duplicates (map forward cells)) <))
         (if (<= (first us) 0) #f
          (let* ([edge (lambda (u)
                         (+ side (apply (if (< side 0) min max)
                           (map (lambda (p) (coord p (- 1 axis)))
                             (filter (lambda (p) (= (forward p) u)) cells)))))]
                 [contour (map (lambda (u) (list u (edge u))) us)]
                 [gap (first us)]
                 [delta (abs (- (second (first contour)) (coord anchor (- 1 axis))))])
           (if (> delta gap) #f (list gap delta j contour)))))))
      (if (null? choices) #f
       (let* ([ordered (sort choices (lambda (a b)
                       (or (< (first a) (first b))
                           (and (= (first a) (first b))
                                (or (< (second a) (second b))
                                    (and (= (second a) (second b)) (< (third a) (third b))))))))]
              [choice (first ordered)])
        (append role (list (fourth choice))))))))
   (define cleared
    (for/fold ([out g]) ([record records])
      (recolor-cells out (obj-cells (list-ref objs (second record))) bg)))
   (for/fold ([out cleared]) ([record records])
    (define source (list-ref objs (second record)))
    (define axis (list-ref record 2))
    (define direction (list-ref record 3))
    (define side (list-ref record 4))
    (define anchor (list-ref record 5))
    (define original-contour (list-ref record 6))
    (define extreme (apply (if (< side 0) min max) (map second original-contour)))
    (define contour (if (eq? contour-mode 'box)
                        (map (lambda (p) (list (first p) extreme)) original-contour)
                        original-contour))
    (define start-u (first (first contour)))
    (define end-u (first (last contour)))
    (define entry-x (second (first contour)))
    (define limit (+ (obj-size source) extra-length))
    (let loop ([u 0] [x (coord anchor (- 1 axis))] [canvas out])
      (if (>= u limit) canvas
       (let* ([next-x
               (cond [(= u 0) x]
                     [(< u start-u) (+ x (cond [(< x entry-x) 1] [(> x entry-x) -1] [else 0]))]
                     [(<= u end-u)
                      (define found (assoc u contour))
                      (if found (second found) x)]
                     [else (- x side)])]
              [p (point (+ (coord anchor axis) (* direction u)) next-x axis)])
        (if (not (in-bounds? (first p) (second p) h w)) canvas
            (loop (+ u 1) next-x (set-cell canvas (first p) (second p) (obj-color source)))))))))))
