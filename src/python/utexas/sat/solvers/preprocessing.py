"""
utexas/sat/solvers/preprocessing.py

@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

from cargo.log               import get_logger
from cargo.temporal          import TimeDelta
from utexas.sat.solvers.base import (
    SAT_Solver,
    SAT_BareResult,
    )

log = get_logger(__name__)

class SAT_PreprocessingSolver(SAT_Solver):
    """
    Execute a solver after a preprocessor pass.
    """

    def __init__(self, preprocessor, solver):
        """
        Initialize.
        """

        SAT_Solver.__init__(self)

        self.preprocessor = preprocessor
        self.inner_solver = solver

    def solve(self, task, cutoff = TimeDelta(seconds = 1e6), seed = None):
        """
        Execute the solver and return its outcome, given a concrete input path.
        """

        from cargo.io import mkdtemp_scoped

        with mkdtemp_scoped(prefix = "sat_preprocessing.") as sandbox_path:
            preprocessed = self.preprocessor.preprocess(task, sandbox_path, cutoff)

            if preprocessed.solver_result is not None:
                # the preprocessor solved the instance
                return \
                    SAT_PreprocessingSolverResult(
                        self,
                        task,
                        preprocessed,
                        None,
                        preprocessed.solver_result.certificate,
                        )
            else:
                # the preprocessor did not solve the instance
                remaining = max(TimeDelta(), cutoff - preprocessed.elapsed)

                if preprocessed.cnf_path is None:
                    # ... it failed unexpectedly
                    result   = self.inner_solver.solve(task, remaining, seed)
                    extended = result.certificate
                else:
                    # ... it generated a new CNF
                    result = self.inner_solver.solve(preprocessed.cnf_path, remaining, seed)

                    if result.certificate is None:
                        extended = None
                    else:
                        extended = preprocessed.extend(result.certificate)

                return \
                    SAT_BareResult(
                        self,
                        task,
                        preprocessed,
                        result,
                        extended,
                        )

