"""
@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

from abc         import abstractmethod
from cargo.log   import get_logger
from cargo.sugar import ABC

log = get_logger(__name__)

def build_strategy(request, trainer):
    """
    Build a selection strategy as requested.
    """

    builders = {
        "sequence" : SequenceStrategy.build,
        "fixed"    : FixedStrategy.build,
        "modeling" : ModelingStrategy.build,
        "bellman"  : BellmanStrategy.build,
        }

    return builders[request["type"]](request, trainer)

class AbstractStrategy(ABC):
    """
    Abstract base for selection strategies.
    """

    @abstractmethod
    def select(self, budget, random):
        """
        A generator that yields actions and receives (outcome, next_budget).
        """

class SequenceStrategy(AbstractStrategy):
    """
    A strategy the follows an iterable sequence for every task.
    """

    def __init__(self, sequence):
        """
        Initialize.
        """

        self._sequence = sequence

    def select(self, budget, random):
        """
        A generator that yields actions and receives (outcome, next_budget).
        """

        for selected in self._sequence:
            if selected.cost <= budget:
                (_, budget) = yield selected
            else:
                break

        while True:
            yield None

    @staticmethod
    def build(request, trainer):
        """
        Build a sequence strategy as requested.
        """

        raise NotImplementedError()

class FixedStrategy(SequenceStrategy):
    """
    A strategy that repeats a fixed action.
    """

    def __init__(self, action):
        """
        Initialize.
        """

        from itertools import repeat

        SequenceStrategy.__init__(self, repeat(action))

    @staticmethod
    def build(request, trainer):
        """
        Build a fixed strategy as requested.
        """

        raise NotImplementedError()

class ModelingStrategy(AbstractStrategy):
    """
    A strategy that employs a model of its actions.
    """

    def __init__(self, model, planner):
        """
        Initialize.
        """

        self._model   = model
        self._planner = planner

    def select(self, budget, random):
        """
        Select an action, yield it, and receive its outcome.
        """

        import numpy

        dimensions = (len(self._model.actions), max(len(a.outcomes) for a in self._model.actions))
        history    = numpy.zeros(dimensions, numpy.uint)

        while True:
            selected          = self._planner.select(self._model, history, budget, random)
            (outcome, budget) = yield selected

            history[self._model.actions.index(selected), selected.outcomes.index(outcome)] += 1

    @staticmethod
    def build(request, trainer):
        """
        Build a modeling selection strategy as requested.
        """

        from borg.portfolio.models   import build_model
        from borg.portfolio.planners import build_planner

        model   = build_model(request["model"], trainer)
        planner = build_planner(request["planner"], trainer)

        return ModelingStrategy(model, planner)

class BellmanStrategy(SequenceStrategy):
    """
    A strategy that employs a model of its actions.
    """

    def __init__(self, model, horizon, budget, discount = 1.0):
        """
        Initialize.
        """

        from cargo.temporal                import TimeDelta
        from borg.portfolio.bellman        import compute_bellman_plan
        from borg.portfolio.decision_world import SolverAction

        plan = compute_bellman_plan(model, horizon, budget, discount)

        plan[-1] = SolverAction(plan[-1].solver, TimeDelta(seconds = 1e6))

        log.info("Bellman plan follows (horizon %i, budget %f)", horizon, budget)

        for (i, action) in enumerate(plan):
            log.info("action %i: %s", i, action.description)

        SequenceStrategy.__init__(self, plan)

    @staticmethod
    def build(request, trainer):
        """
        Build a modeling selection strategy as requested.
        """

        from borg.portfolio.models import build_model

        model = build_model(request["model"], trainer)

        return BellmanStrategy(model, request["horizon"], request["budget"], request["discount"])

