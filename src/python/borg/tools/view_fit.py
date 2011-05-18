"""@author: Bryan Silverthorn <bcs@cargo-cult.org>"""

import plac

if __name__ == "__main__":
    from borg.tools.view_fit import main

    plac.call(main)

import os.path
import json
import cPickle as pickle
import numpy
import scikits.learn.decomposition.pca
import cargo
import borg

logger = cargo.get_logger(__name__, default_level = "INFO")

class CategoryData(object):
    def fit(self, runs_path, budget_interval, budget_count):
        """Fit data for a category."""

        # load the runs data
        logger.info("loading data from %s", runs_path)

        runs = numpy.recfromcsv(runs_path, usemask = True).tolist()

        # build the indices
        solver_index = {}
        instance_index = {}

        for (_, instance, _, _, _, solver_name, _) in runs:
            instance_name = os.path.basename(instance)

            if instance_name not in instance_index:
                instance_index[instance_name] = len(instance_index)
            if solver_name not in solver_index:
                solver_index[solver_name] = len(solver_index)

        S = len(solver_index)
        N = len(instance_index)
        B = budget_count

        self.solvers = sorted(solver_index, key = lambda k: solver_index[k])
        self.instances = sorted(instance_index, key = lambda k: instance_index[k])

        # build the matrices
        budgets = [b * budget_interval for b in xrange(1, B + 1)]
        max_cost = budget_interval * budget_count
        attempts = numpy.zeros((N, S))
        costs = numpy.zeros((N, S))
        successes = numpy.zeros((N, S))
        binned_successes = numpy.zeros((N, S, B))

        for (_, instance, answer, cost, _, solver_name, _) in runs:
            s = solver_index[solver_name]
            n = instance_index[os.path.basename(instance)]

            if attempts[n, s] == 0.0: # XXX support multiple runs
                attempts[n, s] = 1.0
                costs[n, s] = cost

                if cost <= max_cost and not answer.startswith("UNKNOWN"):
                    b = numpy.digitize([cost], budgets)

                    successes[n, s] += 1.0
                    binned_successes[n, s, b] += 1.0

        # fit the model
        self.model = borg.models.BilevelMultinomialModel(binned_successes, attempts)

        # build the mean-cost table
        self.table = []

        for n in xrange(N):
            task_runs_list = []

            for s in xrange(S):
                task_runs_list.append({
                    "solver": self.solvers[s],
                    "cost": costs[n, s],
                    "answer": True if successes[n, s] else None,
                    })

            self.table.append({
                "instance": self.instances[n],
                "runs": task_runs_list,
                })

        # generate cluster projection
        #print self.model._tclass_res_LN.T

        #self.similarity_NN = numpy.dot(self.model._tclass_res_LN.T, self.model._tclass_res_LN)
        #self.similarity_NN = numpy.empty((N, N))

        #for m in xrange(N):
            #for n in xrange(N):
                #self.similarity_NN[m, n] = S - numpy.sum(numpy.abs(successes[m] - successes[n]))

        #kpca = scikits.learn.decomposition.pca.KernelPCA(n_components = 2, kernel = "precomputed")
        #self.projected_N2 = kpca.fit_transform(self.similarity_NN / S)

        return self

class ViewData(object):
    def __init__(self, relative_to, setup):
        self.setup = setup

        # fit a model to each category
        categories = {}

        for category in setup["categories"]:
            path = os.path.join(relative_to, category["file"])

            categories[category["name"]] = \
                CategoryData().fit(
                    path,
                    setup["budget_interval"],
                    setup["budget_count"],
                    )

        self.categories = categories

@plac.annotations(
    out_path = ("path to write model(s)"),
    setup_path = ("path to configuration"),
    )
def main(out_path, setup_path):
    """Prepare to visualize run data."""

    cargo.enable_default_logging()

    # build the configuration
    with open(setup_path) as setup_file:
        setup = json.load(setup_file)

    view = ViewData(os.path.dirname(setup_path), setup)

    # write it to disk
    logger.info("writing visualization data to %s", out_path)

    with open(out_path, "w") as out_file:
        pickle.dump(view, out_file)

