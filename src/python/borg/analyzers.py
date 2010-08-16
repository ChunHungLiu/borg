"""
@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

from abc         import (
    abstractmethod,
    abstractproperty,
    )
from cargo.log   import get_logger
from cargo.sugar import ABC

log = get_logger(__name__)

class Analyzer(ABC):
    """
    Abstract base for task feature acquisition classes.
    """

    @abstractmethod
    def analyze(self, task, environment):
        """
        Acquire features of the specified task.

        @return: Mapping from feature names to feature values.
        """

    @abstractproperty
    def feature_names(self):
        """
        Return the names of features provided by this analyzer.
        """

class NoAnalyzer(Analyzer):
    """
    Acquire no features.
    """

    def analyze(self, task, environment):
        """
        Acquire no features from the specified task.
        """

        return {}

    @property
    def feature_names(self):
        """
        Return the names of features provided by this analyzer.
        """

        return []

class UncompressingAnalyzer(Analyzer):
    """
    Acquire no features.
    """

    def __init__(self, analyzer):
        """
        Initialize.
        """

        self._analyzer = analyzer

    def analyze(self, task, environment):
        """
        Acquire no features from the specified task.
        """

        from borg.tasks import uncompressed_task

        with uncompressed_task(task) as inner_task:
            return self._analyzer.analyze(inner_task, environment)

    @property
    def feature_names(self):
        """
        Return the names of features provided by this analyzer.
        """

        return self._analyzer.feature_names

class SATzillaAnalyzer(Analyzer):
    """
    Acquire features using SATzilla's (old) analyzer.
    """

    def __init__(self, names = None):
        """
        Initialize.
        """

        self._names = names

    def analyze(self, task, environment):
        """
        Acquire features of the specified task.
        """

        # sanity
        from borg.tasks import AbstractFileTask

        assert isinstance(task, AbstractFileTask)

        # compute the features
        from borg.sat.cnf import compute_raw_features

        raw         = compute_raw_features(task.path)
        transformed = {
            "satzilla/vars-clauses-ratio<=1/4.36" : raw["vars-clauses-ratio"] <= (1 / 4.36),
            }

        if self._names is None:
            return transformed
        else:
            return dict((n, transformed[n]) for n in self._names)

    @property
    def feature_names(self):
        """
        Return the names of features provided by this analyzer.
        """

        if self._names is None:
            return ["satzilla/vars-clauses-ratio<=1/4.36"]
        else:
            return self._names

class RecyclingAnalyzer(Analyzer):
    """
    Look up precomputed features from the database.
    """

    def __init__(self, names):
        """
        Initialize.
        """

        self._names = names

    def analyze(self, task, environment):
        """
        Acquire features of the specified task.
        """

        # sanity
        from borg.tasks import AbstractTask

        assert isinstance(task, AbstractTask)

        # look up the features
        with environment.CacheSession() as session:
            from borg.data import TaskFeatureRow as TFR

            constraint = TFR.task == task.get_row(session)

            if self._names is not None:
                constraint = constraint & TFR.name.in_(self._names)

            feature_rows = session.query(TFR.name, TFR.value).filter(constraint).all()

            return dict(feature_rows)

    @property
    def feature_names(self):
        """
        Return the names of features provided by this analyzer.
        """

        return self._names

