import re
PATTERNS = {
    "palace": [r"did NOT converge", r"\bERROR\b", r"\bnan\b"],
    "elmer": [r"Failed convergence", r"NOT converged", r"ERROR::", r"\bNaN\b"],
    "comsol": [r"did not converge", r"\bError\b"],
}

def scan(path, solver):
    pats = [re.compile(p, re.I if solver != "palace" else 0) for p in PATTERNS[solver]]
    return [ln.rstrip() for ln in open(path, errors="replace") if any(p.search(ln) for p in pats)]
