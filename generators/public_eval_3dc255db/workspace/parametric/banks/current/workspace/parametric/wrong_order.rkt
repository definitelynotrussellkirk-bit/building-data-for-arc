(rule!
 ;; Counterfactual: choose the ship with the largest ORIGINAL payload before
 ;; ejection and boundary clipping, then render only that ray.
 (lambda (g)
  (let ()
   (define occupied (filter (lambda (p) (not (= (at g (first p) (second p)) 0))) (grid-positions g)))
   (define (components8 cells)
     (let loop ([remaining cells] [out '()])
       (if (empty? remaining) (reverse out)
           (let* ([start (first remaining)]
                  [region (connected-region g (first start) (second start)
                            (lambda (r c v) (not (= v 0))) 8)])
             (loop (filter (lambda (p) (not (member p region))) remaining) (cons region out))))))
   (define (value p) (at g (first p) (second p)))
   (define (count-color cells color) (count-if (lambda (p) (= (value p) color)) cells))
   (define dirs '((-1 0) (1 0) (0 -1) (0 1)))
   (define (direction cells body)
     (pick-max
      (filter-map
       (lambda (d)
        (let* ([dr (first d)] [dc (second d)]
               [extreme (apply max (map (lambda (p) (+ (* (first p) dr) (* (second p) dc))) body))]
               [tips (filter (lambda (p) (= (+ (* (first p) dr) (* (second p) dc)) extreme)) body)])
         (if (not (= (length tips) 1)) #f
          (let* ([tip (first tips)]
                 [counts (for/list ([depth (in-range 1 5)])
                   (count-if (lambda (p) (member p cells))
                     (for/list ([offset (in-range (- depth) (+ depth 1))])
                       (list (+ (first tip) (* (- dr) depth) (* (- dc) offset))
                             (+ (second tip) (* (- dc) depth) (* dr offset))))))]
                 [cone (apply + counts)]
                 [full (for/sum ([depth (in-range 1 5)] [n (in-list counts)])
                         (if (= n (+ (* 2 depth) 1)) 1 0))]
                 [center (for/sum ([depth (in-range 1 5)])
                   (if (member (list (+ (first tip) (* (- dr) depth))
                                     (+ (second tip) (* (- dc) depth))) cells) 1 0))])
            (list (+ (* cone 100) (* full 10) center) dr dc tip))))) dirs)
      first))
   (define ships
    (filter-map
     (lambda (cells)
      (let ([colors (remove-duplicates (map value cells))])
       (if (not (= (length colors) 2)) #f
        (let* ([body-color (pick-max colors (lambda (c) (count-color cells c)))]
               [payload-color (first (filter (lambda (c) (not (= c body-color))) colors))]
               [body-count (count-color cells body-color)]
               [payload-count (count-color cells payload-color)])
         (if (<= body-count payload-count) #f
          (let* ([body (filter (lambda (p) (= (value p) body-color)) cells)]
                 [payload (filter (lambda (p) (= (value p) payload-color)) cells)]
                 [dir (direction cells body)] [dr (second dir)] [dc (third dir)] [tip (fourth dir)]
                 [ray (filter (lambda (p) (in-bounds? (first p) (second p) h w))
                        (for/list ([step (in-range 1 (+ payload-count 1))])
                          (list (+ (first tip) (* dr step)) (+ (second tip) (* dc step)))))])
            (list cells body-color payload-color payload tip dr dc ray payload-count)))))))
     (components8 occupied)))
   (define selected (pick-max ships (lambda (ship) (list-ref ship 8))))
   (define cleared (for/fold ([out g]) ([ship (in-list ships)])
                     (recolor-cells out (fourth ship) 0)))
   (recolor-cells cleared (list-ref selected 7) (third selected)))))
