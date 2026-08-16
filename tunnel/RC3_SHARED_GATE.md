# RC3 Shared Release Gate

This file intentionally creates one shared branch SHA after the RC3 product, RC3 regression tests, CI workflow, and package workflow have all been updated.

RC3 specifically addresses the physical Monterey failure where reachable meek/obfs4 bridges reached directory bootstrap phases 40-50 but every fallback discarded Tor's directory cache and the controller terminated descriptor loading too aggressively.

The shared gate requires both official workflows to pass on the exact same SHA before the RC3 package may be offered for another physical-Mac run.
