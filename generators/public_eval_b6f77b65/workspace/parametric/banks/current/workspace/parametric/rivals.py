"""Executable support-physics alternatives; errors are not counted as refutations."""
DEPENDENCY={
 'step_a':'Recover and remove the cue-colored pieces, then settle lower posts and beams in bottom-up dependency order.',
 'intermediate':'The already-settled lower support geometry: current post top/bottom rows and beam obstruction rows, with occluded endpoint lengths preserved.',
 'step_b':'Place each higher beam at its earliest lawful row using the current lower supports, then continue the cascade and rasterize the final graph.',
 'why_b_depends_on_a':'Lower beams can fall when their posts are erased, carrying posts that support higher beams. Raw pre-removal post coordinates therefore name unsupported positions; substituting them changes the final upper-beam locations.'
}
WITNESS_SETTING={'support_rule':'both_posts'}


def change(source,old,new):
    if source.count(old)!=1:raise ValueError('rival mutation target must occur exactly once: '+old)
    return source.replace(old,new)


def counterfactual(source):
    return change(source,'(define use-raw-supports #f)','(define use-raw-supports #t)')


def programs(adapter,settings):
    chosen=adapter.program(settings)
    removed="(define removed (remove-duplicates (filter (lambda (v) (not (= v 0))) (first g))))"
    firstcue="(define removed (take (filter (lambda (v) (not (= v 0))) (first g)) 1))"
    no_sides=change(chosen,'[lp (side (- (left o) 1))] [rp (side (+ (right o) 1))]',"[lp '()] [rp '()]")
    return {
      'other_support_rule':adapter.program({'support_rule':'either_post' if settings['support_rule']=='both_posts' else 'both_posts'}),
      'identity':'(rule! (lambda (g) g))',
      'erase_without_settling':'''(rule! (lambda (g)
        (let ([removed (filter (lambda (v) (not (= v 0))) (first g))])
          (grid-from-fn (rows g) (cols g) (lambda (r c)
            (if (and (> r 0) (member (at g r c) removed)) 0 (at g r c)))))))''',
      'independent_column_gravity':'''(rule! (lambda (g)
        (let* ([h (rows g)] [removed (filter (lambda (v) (not (= v 0))) (first g))]
               [columns (for/list ([c (in-range (cols g))])
                 (for/list ([r (in-range 2 h)] #:when (and (not (= (at g r c) 0)) (not (member (at g r c) removed))))
                   (at g r c)))])
          (grid-from-fn h (cols g) (lambda (r c)
            (let* ([vs (list-ref columns c)] [start (- h (length vs))])
              (cond [(= r 0) (at g r c)] [(< r start) 0] [else (list-ref vs (- r start))])))))))''',
      'raw_support_coordinates':counterfactual(chosen),
      'no_occluded_endpoints':change(chosen,'(define hidden (or (= end h) (beam-owned? end c)))','(define hidden #f)'),
      'first_cue_only':change(chosen,removed,firstcue),
      'ignore_side_supports':no_sides,
    }


def intermediate(adapter,pair):
    model=adapter._model;x=pair['input'];removed={v for v in x[0] if v}
    objects=model.extract(x)
    placed=model.settle(objects,len(x),removed,either=False)
    return {'removed_colors':sorted(removed),'extracted_members':objects,
            'settled_members':placed,
            'moved_support_posts':[{'column':p['c'],'color':p['color'],'source_top':p['source_r'],'settled_top':p['r'],'length':p['length']}
                                   for p in placed if p['kind']=='post' and p['source_r']!=p['r']]}
