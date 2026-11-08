(rule!
 ;; The six-row header contains four commands.  A slot's nonzero stripe names a
 ;; body-object color; whether the stripe sits on the slot's left or right side
 ;; specifies the turn hand.  Starting from the same cyan square for every
 ;; command, travel straight to the first axis-aligned target, turn, and continue
 ;; to the edge.  A rectangular blocker redirects toward its farther transverse
 ;; extension.  Missing/non-aligned targets use the straight-up fallback.  Paint
 ;; the union of all cursor footprints and discard the header.
 (lambda (g)
  (let ()
    (define turn-mode 'header)
    (define frame (at g 0 0))
    (define header-end
      (for/first ([r (in-range 1 (rows g))]
                  #:when (andmap (lambda (v) (= v frame)) (list-ref g r))) r))
    (unless header-end (error 'cursor-route "header closing row missing"))
    (define body (subgrid g (+ header-end 1) 0 (- (rows g) 1) (- (cols g) 1)))
    (define h (rows body))
    (define w (cols body))
    (define bg (mode body -1))
    (define nonframe-cols
      (for/list ([c (in-range (cols g))]
                 #:when (for/or ([r (in-range (+ header-end 1))])
                          (not (= (at g r c) frame)))) c))
    (define runs-reversed
      (foldl
       (lambda (c acc)
         (cond [(empty? acc) (list (list c))]
               [(= c (+ 1 (first (first acc))))
                (cons (cons c (first acc)) (rest acc))]
               [else (cons (list c) acc)]))
       '() nonframe-cols))
    (define runs (map reverse (reverse runs-reversed)))
    (unless (= (length runs) 4) (error 'cursor-route "exactly four header slots required"))
    (define commands
      (for/list ([run (in-list runs)])
        (define stripe-values
          (for*/list ([r (in-range 1 header-end)] [c (in-list run)]
                      #:when (let ([v (at g r c)]) (and (not (= v frame)) (not (= v 0)))))
            (at g r c)))
        (when (empty? stripe-values) (error 'cursor-route "header slot lacks a target stripe"))
        (define target (mode-list stripe-values))
        (define target-cols
          (filter (lambda (c) (for/or ([r (in-range 1 header-end)]) (= (at g r c) target))) run))
        (define avg (/ (apply + target-cols) (length target-cols)))
        (define mid (/ (+ (first run) (last run)) 2))
        (list target (if (< avg mid) 'left 'right))))
    (define cursor-cells (find-color body 8))
    (when (empty? cursor-cells) (error 'cursor-route "cyan cursor missing"))
    (define cursor-box (bbox-of-cells cursor-cells))
    (define home-r (first cursor-box))
    (define home-c (second cursor-box))
    (define cursor-size (+ 1 (- (third cursor-box) home-r)))
    (define scene-objects (filter (lambda (obj) (not (= (obj-color obj) 8))) (objects body bg)))
    (define (cursor-cells-at r c)
      (for*/list ([rr (in-range r (+ r cursor-size))]
                  [cc (in-range c (+ c cursor-size))])
        (list rr cc)))
    (define (cursor-in-bounds? r c)
      (and (>= r 0) (>= c 0) (<= (+ r cursor-size) h) (<= (+ c cursor-size) w)))
    (define (cell-in-object? p obj) (and (member p (obj-cells obj)) #t))
    (define (objects-hit r c)
      (filter (lambda (obj)
                (ormap (lambda (p) (cell-in-object? p obj)) (cursor-cells-at r c)))
              scene-objects))
    (define (overlap-count r c obj)
      (count (lambda (p) (cell-in-object? p obj)) (cursor-cells-at r c)))
    (define (dominant-hit r c hits)
      (argmax (lambda (obj) (overlap-count r c obj)) hits))
    (define (turn d hand)
      (define dr (first d))
      (define dc (second d))
      (if (equal? hand 'left) (list (- dc) dr) (list dc (- dr))))
    (define directions (list (list 'up -1 0) (list 'right 0 1) (list 'down 1 0) (list 'left 0 -1)))
    ;; A: decode each command into the ordered top-left positions of its cursor.
    (define routes
      (for/list ([command (in-list commands)])
        (define target (first command))
        (define encoded-hand (second command))
        (define hand
          (if (equal? turn-mode 'reverse)
              (if (equal? encoded-hand 'left) 'right 'left)
              encoded-hand))
        (define aligned
          (filter values
            (for/list ([entry (in-list directions)])
              (define dr (second entry))
              (define dc (third entry))
              (let scan ([r home-r] [c home-c] [steps 0])
                (define nr (+ r dr))
                (define nc (+ c dc))
                (cond
                  [(not (cursor-in-bounds? nr nc)) #f]
                  [else
                   (define hits (objects-hit nr nc))
                   (cond [(empty? hits) (scan nr nc (+ steps 1))]
                         [(ormap (lambda (obj) (= (obj-color obj) target)) hits)
                          (list (+ steps 1) (first entry) dr dc)]
                         [else #f])])))))
        (if (empty? aligned)
            (let fallback ([r home-r] [acc (list (list home-r home-c))])
              (if (cursor-in-bounds? (- r 1) home-c)
                  (fallback (- r 1) (append acc (list (list (- r 1) home-c))))
                  acc))
            (let* ([chosen (argmin first aligned)]
                   [dr0 (third chosen)]
                   [dc0 (fourth chosen)])
              (define-values (arrival-r arrival-c first-positions)
                (let first-leg ([r home-r] [c home-c] [acc (list (list home-r home-c))])
                  (define nr (+ r dr0))
                  (define nc (+ c dc0))
                  (if (or (not (cursor-in-bounds? nr nc)) (not (empty? (objects-hit nr nc))))
                      (values r c acc)
                      (first-leg nr nc (append acc (list (list nr nc)))))))
              (define initial-turn (turn (list dr0 dc0) hand))
              (let second-leg ([r arrival-r] [c arrival-c]
                               [dr (first initial-turn)] [dc (second initial-turn)]
                               [acc first-positions] [seen '()])
                (define state (list r c dr dc))
                (cond
                  [(member state seen) acc]
                  [else
                   (define nr (+ r dr))
                   (define nc (+ c dc))
                   (cond
                     [(not (cursor-in-bounds? nr nc)) acc]
                     [else
                      (define hits (objects-hit nr nc))
                      (if (empty? hits)
                          (second-leg nr nc dr dc (append acc (list (list nr nc))) (cons state seen))
                          (let* ([obj (dominant-hit nr nc hits)]
                                 [box (obj-bbox obj)]
                                 [r0 (first box)] [c0 (second box)]
                                 [r1 (third box)] [c1 (fourth box)]
                                 [next
                                  (if (not (= dr 0))
                                      (let ([left (- c c0)] [right (- c1 (+ c cursor-size -1))])
                                        (if (> left right) (list 0 -1) (list 0 1)))
                                      (let ([up (- r r0)] [down (- r1 (+ r cursor-size -1))])
                                        (if (> up down) (list -1 0) (list 1 0))))])
                            (second-leg r c (first next) (second next) acc (cons state seen))))])]))))))
    ;; B: consume A's positions and paint every occupied cursor cell.
    (for/fold ([out body]) ([route (in-list routes)])
      (for/fold ([painted out]) ([position (in-list route)])
        (paint-cells painted (cursor-cells-at (first position) (second position)) 8))))))
