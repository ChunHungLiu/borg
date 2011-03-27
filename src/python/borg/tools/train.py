"""
@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

import plac

if __name__ == "__main__":
    from borg.tools.train import main

    plac.call(main)

import cPickle as pickle
import cargo
import borg

logger = cargo.get_logger(__name__, default_level = "INFO")

@plac.annotations(
    out_path = ("path to store solver"),
    portfolio_name = ("name of the portfolio to train"),
    domain_name = ("name of the problem domain"),
    tasks_roots = ("paths to training task directories"),
    )
def main(out_path, portfolio_name, domain_name, *tasks_roots):
    """Train a solver."""

    cargo.enable_default_logging()

    # find the training tasks
    domain = borg.get_domain(domain_name)
    train_paths = []
    
    for tasks_root in tasks_roots:
        train_paths.extend(cargo.files_under(tasks_root, domain.extensions))

    logger.info("using %i tasks for training", len(train_paths))

    # train the portfolio
    solver = borg.portfolios.named[portfolio_name](domain, train_paths, 50.0, 36)

    logger.info("portfolio training complete")

    # write it to disk
    with open(out_path, "w") as out_file:
        pickle.dump((domain, solver), out_file, protocol = -1)

    logger.info("portfolio written to %s", out_path)

