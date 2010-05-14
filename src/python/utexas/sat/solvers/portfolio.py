"""
@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

from utexas.sat.solvers import (
    SAT_Solver,
    SAT_BareResult,
    )

class SAT_PortfolioResult(SAT_BareResult):
    """
    Result of a portfolio solver.
    """

    def __init__(self, solver, task, budget, cost, record):
        """
        Initialize.
        """

        if record:
            (_, result) = record[-1]
            satisfiable = result.satisfiable
            certificate = result.certificate
        else:
            satisfiable = None
            certificate = None

        SAT_BareResult.__init__(
            self,
            solver,
            task,
            budget,
            cost,
            satisfiable,
            certificate,
            )

        self._record = record

    @property
    def record(self):
        """
        List of (subsolver, result) pairs.
        """

        return self._record

class SAT_PortfolioSolver(SAT_Solver):
    """
    Solve SAT instances with a portfolio.
    """

    def __init__(self, strategy):
        """
        Initialize.
        """

        self.strategy        = strategy
        self.max_invocations = 50

    def solve(self, task, budget, random, environment):
        """
        Execute the solver and return its outcome, given an input path.
        """

        from cargo.temporal import TimeDelta

        # solve the instance
        remaining = budget
        nleft     = self.max_invocations
        record    = []

        while remaining > TimeDelta() and nleft > 0:
            (action, result)   = self._solve_once_on(task, remaining, random, environment)
            nleft             -= 1

            if action is None:
                break
            else:
                remaining = TimeDelta.from_timedelta(remaining - action.budget)

                record.append((action.solver, result))

                if result.satisfiable is not None:
                    break

        return SAT_PortfolioResult(self, task, budget, budget - remaining, record)

    def _solve_once_on(self, task, budget, random, environment):
        """
        Evaluate once on a specific task.
        """

        # select an action
        action_generator = self.strategy.select(task, budget.as_s)
        action           = action_generator.send(None)

        if action is None:
            return (None, None)
        if action.budget > budget:
            raise RuntimeError("strategy selected an infeasible action")

        # take it, and provide the outcome
        from cargo.temporal             import TimeDelta
        from utexas.portfolio.sat_world import SAT_WorldOutcome

        calibrated = TimeDelta(seconds = action.cost * environment.time_ratio)
        result     = action.solver.solve(task, calibrated, random, environment)
        outcome    = SAT_WorldOutcome.from_result(result)

        try:
            action_generator.send(outcome)
        except StopIteration:
            pass

        return (action, result)

