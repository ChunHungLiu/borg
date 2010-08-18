"""
@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

from cargo.log      import get_logger
from borg.rowed     import Rowed
from borg.solvers   import AbstractSolver

log = get_logger(__name__)

class PreprocessingSolver(Rowed, AbstractSolver):
    """
    Execute a solver after a preprocessor pass.
    """

    def __init__(self, preprocessor, solver):
        """
        Initialize.
        """

        Rowed.__init__(self)

        self._preprocessor = preprocessor
        self._solver       = solver

    def solve(self, task, budget, random, environment):
        """
        Attempt to solve the specified instance.
        """

        from cargo.io import mkdtemp_scoped

        with mkdtemp_scoped(prefix = "preprocessing.") as sandbox_path:
            # preprocess!
            p_attempt = \
                self._preprocessor.preprocess(
                    task,
                    budget,
                    sandbox_path,
                    random,
                    environment,
                    )
            s_attempt = None
            answer    = p_attempt.answer

            if p_attempt.answer is None:
                # the preprocessor did not solve the instance
                from datetime import timedelta

                remaining = max(timedelta(), budget - p_attempt.cost)

                if remaining > timedelta():
                    if p_attempt.output_task == task:
                        # ... it did not generate a preprocessed instance
                        s_attempt = self._solver.solve(task, remaining, random, environment)
                        answer    = s_attempt.answer
                    else:
                        # ... it generated a preprocessed instance
                        s_attempt = \
                            self._solver.solve(
                                p_attempt.output_task,
                                remaining,
                                random,
                                environment,
                                )

                        if s_attempt.answer is not None:
                            answer = \
                                self._preprocessor.extend(
                                    p_attempt.output_task,
                                    s_attempt.answer,
                                    environment,
                                    )
                        else:
                            answer = None

        # return the details of this attempt
        from borg.solvers import PreprocessingAttempt

        return \
            PreprocessingAttempt(
                self,
                task,
                p_attempt,
                s_attempt,
                answer,
                )

