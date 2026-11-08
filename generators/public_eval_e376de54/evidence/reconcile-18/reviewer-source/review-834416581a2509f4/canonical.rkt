(rule!
 (let ()
   (define longest #f)
   (define bg (mode g -1))
   (define h (rows g))
   (define w (cols g))
   (define obs (objects-8 g bg))
   (define sample (first obs))
   (define sample-cells (obj-cells sample))
   (define direction
     (cond
       ((= (obj-h sample) 1) (list 0 1))
       ((= (obj-w sample) 1) (list 1 0))
       ((= (length (remove-duplicates
                     (map (lambda (p) (- (first p) (second p))) sample-cells))) 1)
        (list 1 1))
       (else (list 1 -1))))
   (define dr (first direction))
   (define dc (second direction))
   (define (projection p) (+ (* dr (first p)) (* dc (second p))))
   (define (perpendicular p) (+ (* (- dc) (first p)) (* dr (second p))))
   (define (min-end obj) (pick-min (obj-cells obj) projection))
   (define (max-end obj) (pick-max (obj-cells obj) projection))
   (define min-ends (map min-end obs))
   (define max-ends (map max-end obs))
   (define min-aligned?
     (= (length (remove-duplicates (map projection min-ends))) 1))
   (define max-aligned?
     (= (length (remove-duplicates (map projection max-ends))) 1))
   (define anchor-min? min-aligned?)
   (define (anchor obj) (if anchor-min? (min-end obj) (max-end obj)))
   (define ordered
     (sort obs (lambda (a b) (< (perpendicular (anchor a))
                                (perpendicular (anchor b))))))
   (define target-length
     (if longest
         (apply max (map obj-size obs))
         (obj-size (list-ref ordered (quotient (length ordered) 2)))))
   (define step-r (if anchor-min? dr (- dr)))
   (define step-c (if anchor-min? dc (- dc)))
   (for/fold ((out (empty-grid h w bg))) ((obj ordered))
     (let ((start (anchor obj)))
       (for/fold ((painted out)) ((i (range target-length)))
         (set-cell painted
                   (+ (first start) (* i step-r))
                   (+ (second start) (* i step-c))
                   (obj-color obj)))))))
