"""
@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

import plac

if __name__ == "__main__":
    from borg.tools.run_solvers import main

    plac.call(main)

import os.path
import csv
import cargo
import borg

logger = cargo.get_logger(__name__, default_level = "INFO")

def run_solver_on(solver_name, cnf_path, budget):
    """Run a solver."""

    solver = borg.solvers.named[solver_name]
    (cost, answer) = solver(cnf_path, budget)
    short_answer = None if answer is None else bool(answer)

    logger.info(
        "%s reported %s in %.2f (of %.2f) on %s",
        solver_name,
        short_answer,
        cost,
        budget,
        cnf_path,
        )

    return (solver_name, None, budget, cost, short_answer)

@plac.annotations(
    tasks_root = ("path to task files", "positional", None, os.path.abspath),
    workers = ("submit jobs?", "option", "w", int),
    )
def main(tasks_root, workers = 0):
    """Collect solver running-time data."""

    cargo.enable_default_logging()

    def yield_runs():
        paths = list(cargo.files_under(tasks_root, ["*.cnf"]))

        for _ in xrange(4):
            for solver_name in ["adaptg2wsat++"]:
                for path in paths:
                    yield (run_solver_on, [solver_name, path, 60.0])

    def collect_run((_, arguments), row):
        (_, cnf_path, _) = arguments
        csv_path = cnf_path + ".rtd.csv"
        existed = os.path.exists(csv_path)

        with open(csv_path, "a") as csv_file:
            writer = csv.writer(csv_file)

            if not existed:
                writer.writerow(["solver", "seed", "budget", "cost", "answer"])

            writer.writerow(row)

    cargo.distribute_or_labor(yield_runs(), workers, collect_run)

