(rule!
 ;; Solid colored rectangles are destinations.  For each destination, the
 ;; remaining pixels of its color form a template exactly two rows and two
 ;; columns smaller.  This residual template may be disconnected.
 ;; Keep the destinations' spatial arrangement, cropped with one background
 ;; cell around their union.  Preserve each colored frame and carve its
 ;; template into the interior in the same orientation.  Other colors are
 ;; irrelevant when they do not supply a qualifying destination.
 (lambda (g)
   (let ()
     (define ink-mode 'carve)
     (define association-mode 'color)
     (define background (at g 0 0))
     (define components (objects g background))

     (define (outside-destination? position destination)
       (not (and (<= (obj-r1 destination) (first position) (obj-r2 destination))
                 (<= (obj-c1 destination) (second position) (obj-c2 destination)))))

     (define (template-cells destination)
       (filter (lambda (position) (outside-destination? position destination))
               (find-color g (obj-color destination))))

     (define (qualifies? destination)
       (and (>= (obj-h destination) 4)
            (>= (obj-w destination) 4)
            (= (obj-size destination) (* (obj-h destination) (obj-w destination)))
            (let ((remaining (template-cells destination)))
              (and (not (null? remaining))
                   (let ((box (bbox-of-cells remaining)))
                     (and (= (+ 1 (- (third box) (first box)))
                             (- (obj-h destination) 2))
                          (= (+ 1 (- (fourth box) (second box)))
                             (- (obj-w destination) 2))))))))

     (define candidates (filter qualifies? components))
     (define destinations
       (sort
        (filter
         (lambda (destination)
           (= 1 (length
                 (filter (lambda (other)
                           (= (obj-color other) (obj-color destination)))
                         candidates))))
         candidates)
        (lambda (left right)
          (or (< (obj-r1 left) (obj-r1 right))
              (and (= (obj-r1 left) (obj-r1 right))
                   (< (obj-c1 left) (obj-c1 right)))))))

     ;; Each record is destination object, inclusive source box, boolean mask.
     (define records
       (for/list ((destination (in-list destinations)))
         (let* ((remaining (template-cells destination))
                (box (bbox-of-cells remaining))
                (mask
                 (for/list ((dr (in-range (- (obj-h destination) 2))))
                   (for/list ((dc (in-range (- (obj-w destination) 2))))
                     (if (member (list (+ (first box) dr)
                                       (+ (second box) dc))
                                 remaining)
                         #t
                         #f)))))
           (list destination box mask))))

     (define templates-in-reading-order
       (sort records
             (lambda (left right)
               (let ((left-box (second left)) (right-box (second right)))
                 (or (< (first left-box) (first right-box))
                     (and (= (first left-box) (first right-box))
                          (< (second left-box) (second right-box))))))))

     (if (null? destinations)
         g
         (let* ((top (- (apply min (map obj-r1 destinations)) 1))
                (left (- (apply min (map obj-c1 destinations)) 1))
                (bottom (+ (apply max (map obj-r2 destinations)) 1))
                (right (+ (apply max (map obj-c2 destinations)) 1)))
           (for/fold ((output (subgrid g top left bottom right)))
                     ((record (in-list records))
                      (index (in-range (length records))))
             (define destination (first record))
             (define color (obj-color destination))
             (define selected-template
               (if (eq? association-mode 'color)
                   record
                   (list-ref templates-in-reading-order index)))
             (define mask (third selected-template))
             (for*/fold ((painted output))
                        ((dr (in-range (- (obj-h destination) 2)))
                         (dc (in-range (- (obj-w destination) 2))))
               (define occupied? (list-ref (list-ref mask dr) dc))
               (define value
                 (if (eq? ink-mode 'stamp)
                     (if occupied? color background)
                     (if occupied? background color)))
               (set-cell painted
                         (+ (- (obj-r1 destination) top) 1 dr)
                         (+ (- (obj-c1 destination) left) 1 dc)
                         value))))))))
