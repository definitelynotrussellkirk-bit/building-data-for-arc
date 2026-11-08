;; Workspace prototype for 581bb11ff645; the canonical rule stays authoritative.
;; Replace the placeholders with quoted Racket symbols before execution.
(rule!
 (lambda (g)
   (let* ([h (rows g)]
          [w (cols g)]
          [count-mode __COUNT_MODE__]
          [direction __DIRECTION__]
          [groups (list)]
          [in-grp #f]
          [start 0])
     (define (zero-components c1 c2)
       ;; Each flood is restricted to this group's full-height rectangle.
       ;; Boundary zeros count, and diagonal contact does not join components.
       (define visited (make-hash))
       (define count 0)
       (define (flood! row col)
         (let visit ([pending (list (list row col))])
           (unless (null? pending)
             (let* ([cell (first pending)]
                    [r (first cell)]
                    [c (second cell)]
                    [remaining (rest pending)])
               (if (and (<= 0 r) (< r h)
                        (<= c1 c) (<= c c2)
                        (not (hash-has-key? visited cell))
                        (zero? (at g r c)))
                   (begin
                     (hash-set! visited cell #t)
                     (visit (append (list (list (- r 1) c)
                                          (list (+ r 1) c)
                                          (list r (- c 1))
                                          (list r (+ c 1)))
                                    remaining)))
                   (visit remaining))))))
       (for* ([r (range 0 h)] [c (range c1 (+ c2 1))])
         (when (and (zero? (at g r c))
                    (not (hash-has-key? visited (list r c))))
           (set! count (+ count 1))
           (flood! r c)))
       count)

     ;; Preserve canonical discovery: maximal runs of columns containing red.
     (for ([c (range 0 w)])
       (let ([has-red (for/or ([r (range 0 h)]) (= (at g r c) 2))])
         (cond
           [(and has-red (not in-grp))
            (set! start c)
            (set! in-grp #t)]
           [(and (not has-red) in-grp)
            (set! groups (append groups (list (list start (- c 1)))))
            (set! in-grp #f)])))
     (when in-grp
       (set! groups (append groups (list (list start (- w 1))))))

     (let* ([group-data
             (for/list ([grp groups])
               (let* ([c1 (first grp)]
                      [c2 (second grp)]
                      [score
                       (case count-mode
                         [(cells)
                          (for/sum ([r (range 0 h)])
                            (for/sum ([c (range c1 (+ c2 1))])
                              (if (zero? (at g r c)) 1 0)))]
                         [(components) (zero-components c1 c2)]
                         [else (error 'rule! "unknown count mode: ~a" count-mode)])])
                 (list score c1 c2)))]
            [before?
             (case direction
               [(ascending) <]
               [(descending) >]
               [else (error 'rule! "unknown direction: ~a" direction)])]
            ;; Strict comparison retains the original left-to-right tie order.
            [sorted (sort group-data
                          (lambda (a b) (before? (first a) (first b))))]
            [result (make-hash)])
       (for* ([r (range 0 h)] [c (range 0 w)])
         (hash-set! result (list r c) 0))
       ;; Copy whole source patterns into the original destination slots.
       (for ([i (range 0 (length sorted))])
         (let* ([entry (list-ref sorted i)]
                [src-c1 (second entry)]
                [src-c2 (third entry)]
                [gwidth (+ 1 (- src-c2 src-c1))]
                [dest-grp (list-ref groups i)]
                [dst-c1 (first dest-grp)])
           (for* ([r (range 0 h)] [dc (range 0 gwidth)])
             (hash-set! result (list r (+ dst-c1 dc))
                        (at g r (+ src-c1 dc))))))
       (cellmap g (r c v) (hash-ref result (list r c) 0))))))
