"""
utexas/papers/nips2009/models.py

Various models of task/action outcomes.

@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

import numpy

from cargo.log import get_logger
from cargo.statistics.dcm import DirichletCompoundMultinomial
from cargo.statistics.mixture import FiniteMixture
from utexas.portfolio.world import get_positive_counts
from utexas.portfolio.strategies import ActionModel
from cargo.statistics._statistics import (
    dcm_post_pi_K,
    dcm_model_predict,
    multinomial_model_predict,
    )

log = get_logger(__name__)

class MultinomialActionModel(ActionModel):
    """
    A simple non-mixture multinomial model.
    """

    def __init__(self, world, training):
        """
        Initialize.
        """

        counts       = world.counts_from_events(training)
        total_counts = numpy.sum(counts, 0)
        norm         = numpy.sum(total_counts, 1, numpy.double)[:, numpy.newaxis]

        self.prediction                 = total_counts / norm
        self.prediction.flags.writeable = False

        log.debug("multinomial action model: %s", self.prediction)

    def predict(self, task, history, out = None):
        """
        Return the predicted probability of each outcome of each action given history.
        """

        if out is None:
            out = self.prediction
        else:
            out[:] = self.prediction

        return out

class MultinomialMixtureActionModel(ActionModel):
    """
    An arbitrary mixture model.
    """

    def __init__(self, world, training, estimator):
        """
        Initialize.
        """

        # members
        self.__world = world
        self.__training  = world.counts_from_events(training)
        self.__estimator = estimator

        # model
        counts         = get_positive_counts(self.__training)
        training_split = [counts[:, naction, :] for naction in xrange(world.nactions)]
        self.__mixture = estimator.estimate(training_split)

        # store mixture components in a matrix
        M = self.mixture.ndomains
        K = self.mixture.ncomponents
        D = self.__world.noutcomes

        self.mix_MKD = numpy.empty((M, K, D))

        for m in xrange(M):
            for k in xrange(K):
                self.mix_MKD[m, k] = self.mixture.components[m, k].log_beta

    def predict(self, task, history, out = None):
        """
        Return the predicted probability of each outcome given history.
        """

        # mise en place
        M = self.mixture.ndomains
        K = self.mixture.ncomponents
        D = self.__world.noutcomes

        # get the task-specific history
        history_counts = self.__world.counts_from_events(history)
        counts_MD      = history_counts[task.n]

        # get the outcome probabilities
        if out is None:
            out = numpy.empty((M, D))

        multinomial_model_predict(
            numpy.copy(self.__mixture.pi),
            self.mix_MKD,
            counts_MD,
            out,
            )

        return out

    # properties
    mixture = property(lambda self: self.__mixture)

class DCM_MixtureActionModel(ActionModel):
    """
    A DCM mixture model.
    """

    def __init__(self, world, training, estimator):
        """
        Initialize.
        """

        # members
        self.__world     = world
        self.__training  = world.counts_from_events(training)
        self.__estimator = estimator

        # model
        counts         = get_positive_counts(self.__training)
        training_split = [counts[:, naction, :] for naction in xrange(world.nactions)]
        self.mixture   = estimator.estimate(training_split)

        # cache mixture components as matrices
        M = self.mixture.ndomains
        K = self.mixture.ncomponents
        D = self.__world.noutcomes

        self.sum_MK  = numpy.empty((M, K))
        self.mix_MKD = numpy.empty((M, K, D))

        for m in xrange(M):
            for k in xrange(K):
                component          = self.mixture.components[m, k]
                self.sum_MK[m, k]  = component.sum_alpha
                self.mix_MKD[m, k] = component.alpha

    def get_post_pi_K(self, counts_MD):

        post_pi_K = numpy.copy(self.mixture.pi)

        dcm_post_pi_K(
            post_pi_K,
            self.sum_MK,
            self.mix_MKD,
            counts_MD,
            )

        return post_pi_K

    def predict(self, task, history, out = None):

        # mise en place
        M = self.mixture.ndomains
        K = self.mixture.ncomponents
        D = self.__world.noutcomes

        # get the task-specific history
        history_counts = self.__world.counts_from_events(history)
        counts_MD      = history_counts[task.n]
        post_pi_K      = self.get_post_pi_K(counts_MD)

        # get the outcome probabilities
        if out is None:
            out = numpy.empty((M, D))

        dcm_model_predict(
            post_pi_K,
            numpy.copy(self.sum_MK),
            numpy.copy(self.mix_MKD),
            counts_MD,
            out,
            )

        return out

class OracleActionModel(ActionModel):
    """
    Nosce te ipsum.
    """

    def __init__(self, world):
        """
        Initialize.
        """

        # members
        self.world = world
        self.__last_prediction = (None, None)

    def predict_action(self, task, action):
        """
        Return the predicted probability of C{action} on C{task}.
        """

        counts = numpy.zeros(self.world.noutcomes, dtype = numpy.uint)

        for outcome in self.world.samples.get_outcomes(task, action):
            counts[outcome.n] += 1

        return counts / numpy.sum(counts, dtype = numpy.float)

    def predict(self, task, history, out = None):
        """
        Return the predicted probability of each outcome given history.
        """

        (last_n, last_prediction) = self.__last_prediction

        if last_n == task.n:
            # we already did this
            return last_prediction
        else:
            # calculate the expected utility of each action
            prediction = numpy.empty((self.world.nactions, self.world.noutcomes))

            for action in self.world.actions:
                prediction[action.n] = self.predict_action(task, action)

            # cache
            self.__last_prediction = (task.n, prediction)

            # done
            if out is None:
                return prediction
            else:
                out[:] = prediction

                return out

class RandomActionModel(ActionModel):
    """
    Know nothing.
    """

    def __init__(self, world):
        """
        Initialize.
        """

        # members
        self.world = world

    def predict(self, task, history, out = None):
        """
        Return the predicted probability of each outcome given history.
        """

        if out is None:
            out = numpy.random.random((self.world.nactions, self.world.noutcomes))
        else:
            out[:] = numpy.random.random((self.world.nactions, self.world.noutcomes))

        out /= numpy.sum(out, 1)[:, numpy.newaxis]

        return out

class RankingActionModel(ActionModel):
    """
    Rank actions according to true utility.
    """

    def __init__(self, world, submodel):
        """
        Initialize.
        """

        # members
        self.world = world
        self.submodel = submodel

    def predict(self, task, history, out = None):
        """
        Return the predicted probability of each outcome given history.
        """

        # FIXME use a task_history parameter instead
        # get the task-specific history
        task_history = history.counts[task.n]

#        numpy.uniq?

        if out is None:
            out = FIXME
        else:
            out[:] = FIXME

        return out
