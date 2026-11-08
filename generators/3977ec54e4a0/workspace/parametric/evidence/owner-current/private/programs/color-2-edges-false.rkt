
(rule!
 ;; Green(3) marks sketch V-shaped triangles: an apex plus points along its
 ;; two 45-degree arms (grouped when within Chebyshev distance 2 along a
 ;; row, column, or exact diagonal). For every group, apex, depth and
 ;; orientation where both arms are attested (>=1 mark each, >=3 total,
 ;; and some mark sits at full depth), the whole solid triangle is filled
 ;; with color 2. The marks themselves stay green.
 (lambda (g)
   (let ()
     (define marks (find-color g 3))
     (define max-d (max h w))
     (define (near? a b)  ;; aligned or diagonal within Chebyshev 2
       (let ((dr (abs (- (first a) (first b))))
             (dc (abs (- (second a) (second b)))))
         (and (<= (max dr dc) 2)
              (or (= dr dc) (zero? dr) (zero? dc)))))
     (define groups  ;; connected components of marks under near?
       (for/fold ((gs (list))) ((m marks))
         (let ((touch? (lambda (grp) (any? (lambda (x) (near? m x)) grp))))
           (cons (cons m (apply append (filter touch? gs)))
                 (filter (lambda (grp) (not (touch? grp))) gs)))))
     (define (arm-cell orient ar ac k side)  ;; k-th cell of one arm
       (cond ((zero? orient) (list (+ ar k) (+ ac (if (zero? side) (- k) k))))
             ((= orient 1) (list (- ar k) (+ ac (if (zero? side) (- k) k))))
             ((= orient 2) (list (+ ar (if (zero? side) (- k) k)) (+ ac k)))
             (else (list (+ ar (if (zero? side) (- k) k)) (- ac k)))))
     (define (arm-count orient ar ac d side grp)
       (count-if (lambda (k)
                   (let ((p (arm-cell orient ar ac k side)))
                     (and (in-bounds? (first p) (second p) h w)
                          (member? p grp))))
                 (range 1 (+ d 1))))
     (define (far-supported? orient ar ac d grp)
       (any? (lambda (side)
               (let ((p (arm-cell orient ar ac d side)))
                 (and (in-bounds? (first p) (second p) h w)
                      (member? p grp))))
             (list 0 1)))
     (define (valid? orient apex d grp)
       (let ((a (arm-count orient (first apex) (second apex) d 0 grp))
             (b (arm-count orient (first apex) (second apex) d 1 grp)))
         (and (>= (+ 1 a b) 3) (>= a 1) (>= b 1)
              (far-supported? orient (first apex) (second apex) d grp))))
     (define tris  ;; every attested (orient apex d), over all groups
       (flatmap (lambda (grp)
                  (flatmap (lambda (apex)
                             (flatmap (lambda (d)
                                        (filter values
                                                (map (lambda (orient)
                                                       (and (valid? orient apex d grp)
                                                            (list orient apex d)))
                                                     (list 0 1 2 3))))
                                      (range 1 (+ max-d 1))))
                           grp))
                groups))
     (define (inside? orient apex d r c)  ;; strict diagonal interior; axial depth inclusive
       (let ((ar (first apex)) (ac (second apex)))
         (cond ((zero? orient)
                (and (>= r ar) (<= r (+ ar d))
                     (< (abs (- c ac)) (- r ar))))
               ((= orient 1)
                (and (<= r ar) (>= r (- ar d))
                     (< (abs (- c ac)) (- ar r))))
               ((= orient 2)
                (and (>= c ac) (<= c (+ ac d))
                     (< (abs (- r ar)) (- c ac))))
               (else
                (and (<= c ac) (>= c (- ac d))
                     (< (abs (- r ar)) (- ac c)))))))
     (cellmap g (r c v)
       (if (and (!= v 3)
                (any? (lambda (t)
                        (inside? (first t) (second t) (third t) r c))
                      tris))
           2 v)))))
