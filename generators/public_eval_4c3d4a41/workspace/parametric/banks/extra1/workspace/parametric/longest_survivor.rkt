(rule!
 ;; First perform the gray-scaffold transfer and compute each bar's surviving
 ;; post-clipping cells.  Then retain only the bar with greatest visible length
 ;; (stable left-to-right tie break).  Selection therefore depends on the moved
 ;; intermediate, not on the original bar lengths.
 (lambda (g)
  (let ()
   (define grays
     (filter (lambda (o) (= (obj-color o) 5)) (objects g -1)))
   (define frame (pick-max grays obj-size))
   (define key (pick-min grays obj-size))
   (define fcells (obj-cells frame))
   (define kcells (obj-cells key))
   (define ft (apply min (map first fcells)))
   (define fb (apply max (map first fcells)))
   (define fl (apply min (map second fcells)))
   (define fr (apply max (map second fcells)))
   (define baseline (apply max (map first kcells)))
   (define tooth-cols
     (sort (remove-duplicates
       (map second (filter (lambda (p) (< (first p) baseline)) kcells))) <))
   (define colored
     (filter
       (lambda (p)
         (let ([v (at g (first p) (second p))])
           (and (not (= v 0)) (not (= v 5)))))
       (positions-in-rect (+ ft 1) (+ fl 1) (- fb 1) (- fr 1))))
   (define bar-cols (sort (remove-duplicates (map second colored)) <))
   (define dy (- (- fb 2) baseline))
   (define dx (- (first bar-cols) (first tooth-cols)))
   (define translated
     (map (lambda (p) (list (+ (first p) dy) (+ (second p) dx))) kcells))
   (define records
     (for/list ([tc (in-list tooth-cols)] [bc (in-list bar-cols)])
       (let* ([source (filter (lambda (p) (= (second p) bc)) colored)]
              [color (at g (first (first source)) bc)]
              [tooth (filter (lambda (p) (= (second p) tc)) kcells)]
              [top (+ dy (apply min (map first tooth)))]
              [bottom (- top 1)]
              [targets
               (filter
                 (lambda (p)
                   (and (> (first p) ft) (< (first p) fb)
                        (in-bounds? (first p) (second p) h w)))
                 (for/list ([i (in-range (length source))])
                   (list (- bottom i) bc)))])
         (list tc bc color (length source) targets))))
   (define selected (pick-max records (lambda (record) (length (list-ref record 4)))))
   (define cleared (recolor-cells (recolor-cells g kcells 0) colored 0))
   (define scaffold (recolor-cells cleared translated 5))
   (recolor-cells scaffold (list-ref selected 4) (third selected)))))
