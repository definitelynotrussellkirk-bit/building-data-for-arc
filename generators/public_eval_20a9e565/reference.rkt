(rule!
 ;; Extrapolate the growing sequence of objects into the gray corner window.
 ;; Infer bounding-coordinate recurrences and palette cycles from visible objects.
 ;; Single-color shapes use the smallest consistent periodic/border texture;
 ;; multicolor structures use validated alternating rails or layered arches.
 ;; No supplied grid, gold, task hash, or example index is used by this rule.
 ;; Render the selected future member, then crop the gray-bracket rectangle.
 (lambda (g)
  (let ()
   (define (bb cells) (list (apply min (map first cells)) (apply min (map second cells))
                            (apply max (map first cells)) (apply max (map second cells))))
   (define (bh b) (add1 (- (third b) (first b))))
   (define (bw b) (add1 (- (fourth b) (second b))))
   (define crop (bb (find-color g 5)))
   (define objs (sort (objects-multicolor (recolor g 5 0) 0) <
                      #:key (lambda (o) (* (bh (bb (obj-cells o))) (bw (bb (obj-cells o)))))))
   (define boxes (map (lambda (o) (bb (obj-cells o))) objs))
   (define images (map (lambda (b) (subgrid g (first b) (second b) (third b) (fourth b))) boxes))
   (define (period values)
     (take values (for/first ([p (range 1 (add1 (length values)))]
       #:when (for/and ([v values] [i (in-naturals)]) (= v (list-ref values (remainder i p))))) p)))
   (define (diff values) (map - (rest values) (drop-right values 1)))
   (define (extend values index)
     (if (< index (length values)) (list-ref values index)
       (let* ([ds (diff values)] [dd (diff ds)] [steps (add1 (- index (length values)))]
              [lastv (last values)] [lastd (last ds)])
         (cond [(andmap (lambda (x) (= x (first ds))) ds) (+ lastv (* steps (first ds)))]
               [(andmap (lambda (x) (= x (first dd))) dd) (+ lastv (* steps lastd) (quotient (* (first dd) steps (add1 steps)) 2))]
               [else (let ([p (period ds)])
                 (+ lastv (for/sum ([i (range (length ds) index)]) (list-ref p (remainder i (length p))))))]))))
   (define target-row (for/first ([index (range (length images) (+ (length images) 8))]
       #:do [(define bounds (for/list ([j (range 4)]) (extend (map (lambda (b) (list-ref b j)) boxes) index)))]
       #:when (and (<= (first bounds) (first crop)) (>= (third bounds) (third crop))
                   (<= (second bounds) (second crop)) (>= (fourth bounds) (fourth crop))))
       (list index bounds)))
   (define index (first target-row))
   (define target (second target-row))
   (define th (bh target))
   (define tw (bw target))
   (define palettes (map (lambda (im) (grid-colors im 0)) images))
   (define fs (append (list (list 'constant 0))
     (for*/list ([kind '(top bottom)] [p (range 1 5)]) (list kind p))
     (for*/list ([kind '(local-mod global-mod center-mod)] [p (range 2 9)]) (list kind p))))
   (define (feature desc local size origin)
     (let ([kind (first desc)] [p (second desc)])
       (cond [(eq? kind 'constant) 0] [(eq? kind 'top) (min local p)]
             [(eq? kind 'bottom) (min (- size 1 local) p)]
             [(eq? kind 'local-mod) (modulo local p)]
             [(eq? kind 'global-mod) (modulo (+ origin local) p)]
             [else (modulo (+ (* 2 local) (- size) 1) p)])))
   (define (lex< a b)
     (cond [(empty? a) #f] [(< (first a) (first b)) #t]
           [(> (first a) (first b)) #f] [else (lex< (rest a) (rest b))]))
   (define observations (apply append (for/list ([im images] [bounds boxes])
     (for*/list ([r (range (rows im))] [c (range (cols im))])
       (list r c (rows im) (cols im) (first bounds) (second bounds) (if (= (at im r c) 0) 0 1))))))
   (define (learn rf cf)
     (let fill ([remaining observations] [table (hash)])
       (if (empty? remaining) table
         (let* ([p (first remaining)]
                [key (list (feature rf (list-ref p 0) (list-ref p 2) (list-ref p 4))
                           (feature cf (list-ref p 1) (list-ref p 3) (list-ref p 5)))]
                [v (list-ref p 6)] [old (hash-ref table key -1)])
           (and (or (= old -1) (= old v)) (fill (rest remaining) (hash-set table key v)))))))
   (define (texture)
     (define candidates (filter identity (for*/list ([fi (range (length fs))] [fj (range (length fs))])
       (define rf (list-ref fs fi)) (define cf (list-ref fs fj)) (define table (learn rf cf))
       (and table
         (for*/and ([r (range th)] [c (range tw)])
           (hash-has-key? table (list (feature rf r th (first target)) (feature cf c tw (second target)))))
         (list (list (hash-count table) (+ (second rf) (second cf)) (+ fi fj) fi fj) rf cf table)))))
     (define chosen (first (sort candidates lex< #:key first)))
     (define colors (period (map first palettes)))
     (define color (list-ref colors (remainder index (length colors))))
     (grid-from-fn th tw (lambda (r c)
       (* color (hash-ref (fourth chosen)
         (list (feature (second chosen) r th (first target)) (feature (third chosen) c tw (second target))))))))
   (define (chain count colors phase)
     (define height (sub1 (* 4 count))) (define center (sub1 (* 2 count)))
     (grid-from-fn height 2 (lambda (r c)
       (define distance (abs (- r center))) (define t (quotient distance 2))
       (define inner (list-ref colors (remainder t (length colors))))
       (if (even? distance) inner
         (if (= c (modulo (+ phase t) 2)) inner
           (if (< (add1 t) count) (list-ref colors (remainder (add1 t) (length colors))) 0))))))
   (define (arch count colors)
     (define width (add1 (* 4 count)))
     (grid-from-fn (* 2 count) width (lambda (r c)
       (define t (quotient r 2)) (define left (* 2 (- count 1 t))) (define right (- width 1 left))
       (define color (list-ref colors (remainder (- count 1 t) (length colors))))
       (cond [(and (= t 0) (= r 0) (and (<= left c) (<= c right))) color]
             [(and (= t 0) (= r 1) (or (= c left) (= c right))) color]
             [(and (> t 0) (even? r) (or (and (<= left c) (<= c (+ left 2))) (and (<= (- right 2) c) (<= c right)))) color]
             [(and (> t 0) (odd? r) (or (= c left) (= c right))) color]
             [(and (> t 0) (odd? r) (or (= c (+ left 2)) (= c (- right 2))))
              (list-ref colors (remainder (- count t) (length colors)))]
             [else 0]))))
   (define predicted
     (cond [(andmap (lambda (cs) (= (length cs) 1)) palettes) (texture)]
           [(and (= tw 2) (= (modulo th 4) 3)
                 (andmap (lambda (im) (and (= (cols im) 2) (= (modulo (rows im) 4) 3))) images))
            (let* ([big (last images)] [count (quotient (add1 (rows big)) 4)] [middle (quotient (rows big) 2)]
                   [colors (period (for/list ([t (range count)]) (at big (+ middle (* 2 t)) 0)))]
                   [phase (for/first ([p '(0 1)] #:when
                     (andmap (lambda (im) (equal? im (chain (quotient (add1 (rows im)) 4) colors p))) images)) p)])
              (chain (quotient (add1 th) 4) colors phase))]
           [else
            (let* ([big (last images)] [count (quotient (rows big) 2)]
                   [colors (period (for/list ([t (range count)]) (at big (* 2 (- count 1 t)) (* 2 t))))])
              (arch (quotient th 2) colors))]))
   (define cropped (subgrid predicted (- (first crop) (first target)) (- (second crop) (second target))
                                     (- (third crop) (first target)) (- (fourth crop) (second target))))
   cropped)))
