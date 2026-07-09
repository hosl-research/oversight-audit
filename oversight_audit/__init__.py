"""
oversight-audit: does your AI-review logging record process, or function?

The core claim (see README): a standard audit trail records that a review
happened -- reviewer, item, decision, timestamp, approval -- and that record is
identical whether the reviewer engaged fully or rubber-stamped. This package
does not pretend to recover engagement from a record that cannot carry it.
It does two honest things:

  1. demo: generate two populations of reviewers (engaged and procedural) with
     known ground truth, then show that the fields a standard audit trail keeps
     separate them at chance, while function-level signals a standard trail does
     not keep separate them cleanly.

  2. check: audit a review-log SCHEMA (the fields you actually capture) and
     report which function-level oversight signals you can and cannot compute
     from it -- that is, what would change in your record if a reviewer stopped
     looking.
"""

__version__ = "0.1.0"
