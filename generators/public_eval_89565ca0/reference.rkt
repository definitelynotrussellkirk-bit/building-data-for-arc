(rule!
 ;; Restore each color's supported rectangular wall network through nonzero
 ;; occlusions. Count its enclosed four-connected interior regions, then render
 ;; one row per structure in room-count order, padded with the noise color.
 ;; Equal counts use leftmost bbox, then topmost bbox, then color. This spatial
 ;; tie convention is an explicit extension of the supplied examples.
 (lambda (g)
  (let ()
   (define descending? #f)
   (define present-colors (grid-colors g 0))
   ;; Color info: color, top, left, bottom, right, H axes, V axes.
   (define (describe-color color)
    (define pixels (find-color g color))
    (define top (apply min (map first pixels)))
    (define left (apply min (map second pixels)))
    (define bottom (apply max (map first pixels)))
    (define right (apply max (map second pixels)))
    (define horizontal-axes
     (for/list ([rr (range top (+ bottom 1))]
      #:when (or (= rr top) (= rr bottom)
       (for/or ([cc (range left right)])
        (and (= (at g rr cc) color) (= (at g rr (+ cc 1)) color))))) rr))
    (define vertical-axes
     (for/list ([cc (range left (+ right 1))]
      #:when (or (= cc left) (= cc right)
       (for/or ([rr (range top bottom)])
        (and (= (at g rr cc) color) (= (at g (+ rr 1) cc) color))))) cc))
    (list color top left bottom right horizontal-axes vertical-axes))
   (define color-infos (map describe-color present-colors))
   (define (off-axis? info)
    (for/or ([pixel (find-color g (first info))])
     (and (not (member (first pixel) (list-ref info 5)))
          (not (member (second pixel) (list-ref info 6))))))
   (define noise-info (first (filter off-axis? color-infos)))
   (define noise-color (first noise-info))
   (define structure-infos
    (filter (lambda (info) (not (= (first info) noise-color))) color-infos))
   (define (measure-structure info)
    (define color (first info))
    (define top (list-ref info 1))
    (define left (list-ref info 2))
    (define bottom (list-ref info 3))
    (define right (list-ref info 4))
    (define horizontal-axes (list-ref info 5))
    (define vertical-axes (list-ref info 6))
    (define box-height (+ 1 (- bottom top)))
    (define box-width (+ 1 (- right left)))
    ;; Only a strict interior own-color witness supports an elementary wall.
    (define (interval-pixel? rr cc) (= (at g rr cc) color))
    (define (horizontal-supported? rr lo hi)
     (for/or ([cc (range (+ lo 1) hi)]) (interval-pixel? rr cc)))
    (define (vertical-supported? cc lo hi)
     (for/or ([rr (range (+ lo 1) hi)]) (interval-pixel? rr cc)))
    (define horizontal-intervals
     (for*/list ([rr horizontal-axes] [index (range 0 (- (length vertical-axes) 1))]
      #:when (horizontal-supported? rr (list-ref vertical-axes index)
                                       (list-ref vertical-axes (+ index 1))))
      (list rr (list-ref vertical-axes index) (list-ref vertical-axes (+ index 1)))))
    (define vertical-intervals
     (for*/list ([cc vertical-axes] [index (range 0 (- (length horizontal-axes) 1))]
      #:when (vertical-supported? cc (list-ref horizontal-axes index)
                                     (list-ref horizontal-axes (+ index 1))))
      (list cc (list-ref horizontal-axes index) (list-ref horizontal-axes (+ index 1)))))
    (define (restored-wall? rr cc)
     (or (= rr top) (= rr bottom) (= cc left) (= cc right)
      (for/or ([segment horizontal-intervals])
       (and (= rr (first segment)) (<= (second segment) cc) (<= cc (third segment))))
      (for/or ([segment vertical-intervals])
       (and (= cc (first segment)) (<= (second segment) rr) (<= rr (third segment))))))
    (define restored-walls
     (build-grid box-height box-width (r c)
      (if (restored-wall? (+ top r) (+ left c)) 1 0)))
    (define raw-walls
     (build-grid box-height box-width (r c)
      (if (= (at g (+ top r) (+ left c)) color) 1 0)))
    (define count-walls restored-walls)
    (define interior-free
     (build-grid box-height box-width (r c)
      (if (and (> r 0) (< r (- box-height 1)) (> c 0) (< c (- box-width 1))
               (= (at count-walls r c) 0)) 1 0)))
    (define region-count (length (objects interior-free 0)))
    (define room-count region-count)
    ;; Output record: color, room count, bbox left, bbox top, bbox area.
    (list color room-count left top (* box-height box-width)))
   (define records (map measure-structure structure-infos))
   (define (spatial-before? a b)
    (cond
     [(not (= (list-ref a 2) (list-ref b 2))) (< (list-ref a 2) (list-ref b 2))]
     [(not (= (list-ref a 3) (list-ref b 3))) (< (list-ref a 3) (list-ref b 3))]
     [else (< (first a) (first b))]))
   (define (before? a b)
    (cond
     [(= (second a) (second b)) (spatial-before? a b)]
     [descending? (> (second a) (second b))]
     [else (< (second a) (second b))]))
   (define ordered-records (sort records before?))
   (define output-width (apply max (map second records)))
   (define padding-color noise-color)
   (define output
    (build-grid (length ordered-records) output-width (r c)
     (let ([record (list-ref ordered-records r)])
      (if (< c (second record)) (first record) padding-color))))
   (define final-output output)
   final-output)))
