(rule!
 ;; Separator-bounded top panels are monochrome templates. The middle panels
 ;; overlay a color-coded placement blueprint. Bottom singletons map each top
 ;; template to its output color. Expand every blueprint cell into the matching
 ;; template mask, recolored by that template's singleton.
 (lambda (g)
  (let ()
   (define scope-mode 0)
   (define five-counts
    (for/list ((r (range (rows g))))
     (count-if (lambda (v) (= v 5)) (row g r))))
   (define separator-rows
    (filter (lambda (r) (> (list-ref five-counts r) 4))
            (range (rows g))))
   (define size (first separator-rows))
   (define lower-separator (second separator-rows))
   (define starts
    (filter
     (lambda (start)
      (for*/or ((r (range size)) (c (range start (+ start size))))
       (let ((v (at g r c))) (and (!= v 0) (!= v 5)))))
     (range 0 (- (+ (cols g) 1) size) (+ size 1))))
   (define (panel-color start)
    (first
     (remove-duplicates
      (for*/list ((r (range size)) (c (range start (+ start size)))
                  #:when (let ((v (at g r c))) (and (!= v 0) (!= v 5))))
       (at g r c)))))
   (define (legend-color start)
    (first
     (remove-duplicates
      (for*/list ((r (range (+ lower-separator 1) (rows g)))
                  (c (range start (+ start size)))
                  #:when (let ((v (at g r c))) (and (!= v 0) (!= v 5))))
       (at g r c)))))
   (define records
    (for/list ((start starts))
     (list start (panel-color start) (legend-color start))))
   (define placements
    (for*/list ((start starts) (r (range size)) (c (range size))
                #:when (let ((v (at g (+ size 1 r) (+ start c))))
                         (and (!= v 0) (!= v 5))))
     (list r c (at g (+ size 1 r) (+ start c)))))
   (define modal-record
    (pick-max records
     (lambda (record)
      (count-if (lambda (placement) (= (third placement) (second record)))
                placements))))
   (define modal-color (second modal-record))
   (build-grid (* size size) (* size size) (r c)
    (let* ((macro-r (quotient r size))
           (macro-c (quotient c size))
           (placement
            (for/first ((p placements)
                        #:when (and (= (first p) macro-r) (= (second p) macro-c))) p)))
     (if (or (not placement)
             (and (= scope-mode 1) (!= (third placement) modal-color)))
         0
         (let* ((record
                 (for/first ((x records) #:when (= (second x) (third placement))) x))
                (source (at g (modulo r size) (+ (first record) (modulo c size)))))
          (if (= source 0) 0 (third record)))))))))
