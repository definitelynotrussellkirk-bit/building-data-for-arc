(rule!
 ;; The green L FRAME at the top-left encloses the KEY color set.
 ;; Mixed-color PANELS are 4-connected non-orange regions outside that frame.
 ;; Erase a panel into orange when it contains every distinct key color;
 ;; repetitions and additional colors do not change this canonical test.
 ;; The optional cascade propagates from those complete matches through shared
 ;; non-key marker colors until no additional panel can be reached.
 (lambda (g)
   (let ()
     (define erase-policy "matching")
     (define initial-scope "seeds")
     (define frame-h (for/first ((r (range h)) #:when (= (at g r 0) 3)) r))
     (define frame-w (for/first ((c (range w)) #:when (= (at g 0 c) 3)) c))
     (define keys
       (remove-duplicates
        (filter (lambda (v) (not (member v '(0 3 7))))
                (apply append (subgrid g 0 0 (- frame-h 1) (- frame-w 1))))))
     (define mask
       (build-grid h w (r c)
         (if (and (not (and (<= r frame-h) (<= c frame-w)))
                  (not (= (at g r c) 7))) 1 7)))
     (define panels (objects mask 7))
     (define (palette o)
       (remove-duplicates
        (filter (lambda (v) (not (= v 0)))
                (map (lambda (p) (at g (first p) (second p))) (obj-cells o)))))
     (define (extra-colors o)
       (filter (lambda (v) (not (member v keys))) (palette o)))
     (define seeds
       (filter (lambda (o) (andmap (lambda (k) (member k (palette o))) keys)) panels))
     (define (expand selected)
       (define active
         (remove-duplicates
          (apply append
                 (map extra-colors (if (equal? initial-scope "global") panels selected)))))
       (filter (lambda (o)
                 (or (member o selected)
                     (ormap (lambda (v) (member v active)) (extra-colors o)))) panels))
     (define selected
       (if (equal? erase-policy "matching") seeds
           (let loop ((selected seeds))
             (define next (expand selected))
             (if (= (length next) (length selected)) selected (loop next)))))
     (for/fold ((out g)) ((o selected))
       (recolor-cells out (obj-cells o) 7)))))
