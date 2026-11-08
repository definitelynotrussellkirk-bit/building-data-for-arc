(rule!
 (lambda (g)
  (let ()
   ;; Find the repeated non-background full-line color, split only on that
   ;; color, infer the unique boundary-port chain, then stack the unchanged
   ;; panels from its open source end to its open sink end.
   (define reverse-chain #f)
   (define bg (mode g -1))
   (define lines
    (filter (lambda (info) (not (= (third info) bg)))
            (internal-separators g)))
   (define line-colors (remove-duplicates (map third lines)))
   (define sep
    (pick-max line-colors
              (lambda (color)
               (count-if (lambda (info) (= (third info) color)) lines))))
   (define row-cuts
    (sort (map second
               (filter (lambda (info)
                        (and (eq? (first info) 'row) (= (third info) sep)))
                       lines)) <))
   (define col-cuts
    (sort (map second
               (filter (lambda (info)
                        (and (eq? (first info) 'col) (= (third info) sep)))
                       lines)) <))
   (define (bands n cuts)
    (let loop ([start 0] [remaining cuts] [answer '()])
     (if (null? remaining)
         (reverse (if (< start n) (cons (list start (- n 1)) answer) answer))
         (let ([cut (first remaining)])
          (loop (+ cut 1) (rest remaining)
                (if (< start cut) (cons (list start (- cut 1)) answer) answer))))))
   (define row-bands (bands h row-cuts))
   (define col-bands (bands w col-cuts))
   (define panels
    (apply append
     (for/list ([rb (in-list row-bands)])
      (for/list ([cb (in-list col-bands)])
       (subgrid g (first rb) (first cb) (second rb) (second cb))))))
   (define (edge panel side)
    (cond
     [(eq? side 'top)
      (for/list ([c (in-range (cols panel))]
                 #:when (not (= (at panel 0 c) bg))) c)]
     [(eq? side 'bottom)
      (for/list ([c (in-range (cols panel))]
                 #:when (not (= (at panel (- (rows panel) 1) c) bg))) c)]
     [(eq? side 'left)
      (for/list ([r (in-range (rows panel))]
                 #:when (not (= (at panel r 0) bg))) r)]
     [else
      (for/list ([r (in-range (rows panel))]
                 #:when (not (= (at panel r (- (cols panel) 1)) bg))) r)]))
   (define vertical-score
    (for/sum ([panel (in-list panels)])
     (+ (length (edge panel 'top)) (length (edge panel 'bottom)))))
   (define horizontal-score
    (for/sum ([panel (in-list panels)])
     (+ (length (edge panel 'left)) (length (edge panel 'right)))))
   (define vertical? (> vertical-score horizontal-score))
   ;; Each record is (input-index panel incoming-port outgoing-port).
   (define records
    (for/list ([panel (in-list panels)] [index (in-naturals)])
     (list index panel
           (edge panel (if vertical? 'top 'left))
           (edge panel (if vertical? 'bottom 'right)))))
   (define starts (filter (lambda (record) (null? (third record))) records))
   (define (walk path remaining)
    (define outgoing (fourth (last path)))
    (if (null? remaining)
        (if (null? outgoing) (list path) '())
        (apply append
         (for/list ([candidate (in-list remaining)]
                    #:when (equal? (third candidate) outgoing))
          (walk (append path (list candidate)) (remove candidate remaining))))))
   (define start (first starts))
   (define solutions (walk (list start) (remove start records)))
   (define forward (first solutions))
   (define chosen (if reverse-chain (reverse forward) forward))
   (define ordered (map second chosen))
   (define separator
    (if vertical?
        (empty-grid 1 (cols (first ordered)) sep)
        (empty-grid (rows (first ordered)) 1 sep)))
   (define (with-separators xs)
    (if (null? (rest xs)) xs
        (cons (first xs) (cons separator (with-separators (rest xs))))))
   (stack-grids (if vertical? 'vertical 'horizontal)
                (with-separators ordered)))))
