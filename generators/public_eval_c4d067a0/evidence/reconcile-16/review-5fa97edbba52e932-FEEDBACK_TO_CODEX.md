# F1: Biggest avoidable friction: public creation IDs cannot reach ordinary generation

The creation API issues `public_eval_<8hex>` identifiers but the shared runner's
hex-only rule-ID guard rejects them even after registration; admit precisely that
namespace and add a copied-runtime public-creation regression before issuing new
packets. A minimal proposed patch and RED/GREEN 22-case reproducer are included
in checks/, with no shared-source edit or owner-approval claim.
