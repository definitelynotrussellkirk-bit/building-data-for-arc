(rule!
 ;; A red tail identifies the launch direction at the yellow emitter.
 ;; Trace each beam until the first blue/green relay. Reached relays become red
 ;; and launch parallel beams outward from their green boundary port.
 ;; Unreached relays disappear. Re-entering an activated relay terminates that
 ;; beam; breadth-first activation assigns minimum relay-hop depths.
 (lambda (g)
   (let ()
     (define mask (grid-from-fn h w (lambda (r c) (if (member (at g r c) '(1 3)) 1 0))))
     (define obs (objects mask 0))
     (define ids (range (length obs)))
     (define gun (first (find-color g 4)))
     (define launch
       (first (filter (lambda (d)
         (let ((rr (- (first gun) (first d))) (cc (- (second gun) (second d))))
           (and (<= 0 rr) (< rr h) (<= 0 cc) (< cc w) (= (at g rr cc) 2)))) cardinal-deltas)))
     (define (port o) (filter (lambda (p) (= (at g (first p) (second p)) 3)) (obj-cells o)))
     (define (exit-dir o)
       (let ((ps (port o)))
         (cond ((andmap (lambda (p) (= (first p) (obj-r1 o))) ps) '(-1 0))
               ((andmap (lambda (p) (= (first p) (obj-r2 o))) ps) '(1 0))
               ((andmap (lambda (p) (= (second p) (obj-c1 o))) ps) '(0 -1))
               (else '(0 1)))))
     (define (walk rr cc dr dc cells)
       (if (or (< rr 0) (>= rr h) (< cc 0) (>= cc w)) (list cells #f)
         (let* ((p (list rr cc))
                (hit (find-first (lambda (i) (member p (obj-cells (list-ref obs i)))) ids))
                (new (cons p cells)))
           (if hit (list new hit) (walk (+ rr dr) (+ cc dc) dr dc new)))))
     (define initial (grid-from-fn h w (lambda (r c) (if (member (at g r c) '(2 4)) 2 8))))
     (define state
       (let loop ((queue (list (list gun launch 0))) (depths (map (lambda (i) -1) ids)) (out initial))
         (if (null? queue) (list out depths)
           (let* ((item (first queue)) (p (first item)) (d (second item)) (depth (third item))
                  (ray (walk (+ (first p) (first d)) (+ (second p) (second d)) (first d) (second d) '()))
                  (hit (second ray)) (painted (recolor-cells out (first ray) 2)))
             (if (or (not hit) (>= (list-ref depths hit) 0))
                 (loop (rest queue) depths painted)
                 (let* ((o (list-ref obs hit)) (next-depth (+ depth 1))
                        (next-d (map (lambda (i) (if (= i hit) next-depth (list-ref depths i))) ids))
                        (emitted (map (lambda (p) (list p (exit-dir o) next-depth)) (port o))))
                   (loop (append (rest queue) emitted) next-d (recolor-cells painted (obj-cells o) 2))))))))
     (define result (first state))
     (define depths (second state))
     (define reached (filter (lambda (i) (> (list-ref depths i) 0)) ids))
     ;; Deliberately wrong: choose nodes with no outgoing object hit, rather
     ;; than maximum minimum-hop depth. A cycle distinguishes the two rules.
     (define terminals
       (filter (lambda (i)
         (let* ((o (list-ref obs i)) (d (exit-dir o)))
           (andmap (lambda (p)
             (not (second (walk (+ (first p) (first d))
                                (+ (second p) (second d))
                                (first d) (second d) '())))) (port o)))) reached))
     (recolor-cells result
       (flatmap (lambda (i) (obj-cells (list-ref obs i))) terminals) 9))))
