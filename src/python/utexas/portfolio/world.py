"""
utexas/portfolio/world.py

Actions, tasks, outcomes, and other pieces of the world.

@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

from abc         import abstractproperty
from cargo.sugar import ABC

class Action(ABC):
    """
    An action in the world.
    """

    @property
    def description(self):
        """
        A human-readable description of this action.
        """

    @abstractproperty
    def cost(self):
        """
        The typical cost of taking this action.
        """

class Outcome(ABC):
    """
    An outcome of an action in the world.
    """

    pass

