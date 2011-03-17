"""@author: Bryan Silverthorn <bcs@cargo-cult.org>"""

class PseudoBooleanInstance(object):
    def __init__(self, N, constraints, objective = None):
        self.N = N
        self.constraints = constraints
        self.objective = objective

def parse_opb_file(opb_file):
    """Parse a pseudo-Boolean satisfaction problem."""

    # prepare constraint parsing
    def parse_terms(parts):
        weight = None
        literals = []
        relation = None
        terms = []

        for part in parts:
            if part[0] == "~" or part[0] == "x":
                literal = int(part[1:])

                if part[0] == "~":
                    literal *= -1

                literals.append(literal)
            else:
                if weight is not None:
                    terms.append((weight, literals))

                    literals = []

                weight = int(part)

        terms.append((weight, literals))

        return terms

    # parse all lines
    constraints = []
    objective = None

    for line in opb_file:
        if line.startswith("*"):
            # comment line
            continue
        elif line.startswith("min:"):
            # objective line
            if objective is not None:
                raise RuntimeError("multiple objectives in PB input")

            objective = parse_terms(line[4:-1].split())
        else:
            # constraint line
            parts = line[:-2].split()
            terms = parse_terms(parts[:-2])
            relation = parts[-2]
            value = int(parts[-1])

            constraints.append((terms, relation, value))

    # compute basic properties
    N = 0

    for (terms, _, _) in constraints:
        for (_, literals) in terms:
            N = max(N, max(abs(l) for l in literals))

    # ...
    return PseudoBooleanInstance(N, constraints, objective)

