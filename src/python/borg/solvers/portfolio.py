"""
@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

from cargo.log    import get_logger
from borg.rowed   import Rowed
from borg.solvers import (
    RunAttempt,
    AbstractSolver,
    )

log = get_logger(__name__)

# FIXME hack---shouldn't really be a RunAttempt
# FIXME (if the *only* distinction between a run and non-run attempt
# FIXME  is the presence of an associated process run, why bother with
# FIXME  the distinction? just have a nullable column)
class PortfolioAttempt(RunAttempt):
    """
    Result of a portfolio solver.
    """

    def __init__(self, solver, task, budget, cost, record):
        """
        Initialize.
        """

        from cargo.unix.accounting import CPU_LimitedRun

        if record:
            (_, attempt) = record[-1]
            answer       = attempt.answer
        else:
            answer = None

        RunAttempt.__init__(
            self,
            solver,
            task,
            answer,
            None,
            CPU_LimitedRun(None, budget, None, None, None, cost, None, None),
            )

        self._record = record

    @property
    def record(self):
        """
        List of (subsolver, result) pairs.
        """

        return self._record

class PortfolioSolver(Rowed, AbstractSolver):
    """
    Solve tasks with a portfolio.
    """

    def __init__(self, strategy, analyzer):
        """
        Initialize.
        """

        Rowed.__init__(self)

        self._strategy        = strategy
        self._analyzer        = analyzer
        self._max_invocations = 50

    def solve(self, task, budget, random, environment):
        """
        Execute the solver and return its outcome, given an input path.
        """

        # first, compute features
        features = self._analyzer.analyze(task, environment)

        for (name, value) in features.items():
            log.detail("feature %s has value %s", name, value)

        # then invoke solvers
        from cargo.temporal       import TimeDelta
        from borg.portfolio.world import (
            SolverAction,
            FeatureAction,
            )

        remaining = budget
        nleft     = self._max_invocations
        record    = []

        self._strategy.reset()

        while remaining > TimeDelta() and nleft > 0:
            # select an action
            log.debug("selecting an action with %s remaining", remaining)

            action = self._strategy.choose(remaining.as_s, random)

            # take the action
            if action is None:
                break
            elif isinstance(action, FeatureAction):
                log.info("taking feature action %s", action.description)

                outcome = action.take(features)
            elif isinstance(action, SolverAction):
                log.info("taking solver action %s", action.description)

                (attempt, outcome)  = action.take(task, remaining, random, environment)
                nleft              -= 1
                remaining           = TimeDelta.from_timedelta(remaining - action.budget)

                record.append((action.solver, attempt))

                if outcome.utility > 0.0:
                    break
            else:
                raise TypeError("cannot handle unexpected action type")

            # witness its outcome
            self._strategy.see(action, outcome)

        return PortfolioAttempt(self, task, budget, budget - remaining, record)

    def get_new_row(self, session):
        """
        Create or obtain an ORM row for this object.
        """

        from borg.data import SolverRow

        solver_row = session.query(SolverRow).get(self.name)

        if solver_row is None:
            solver_row = SolverRow(name = self.name, type = "sat")

            session.add(solver_row)

        return solver_row

    @property
    def name(self):
        """
        A name for this solver.
        """

        return "portfolio"

    @property
    def analyzer(self):
        """
        Return the analyzer employed.
        """

        return self._analyzer
 
