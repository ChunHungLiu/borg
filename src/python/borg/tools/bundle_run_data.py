"""@author: Bryan Silverthorn <bcs@cargo-cult.org>"""

import plac
import borg

if __name__ == "__main__":
    plac.call(borg.tools.bundle_run_data.main)

import os
import os.path
import csv
import cargo

logger = cargo.get_logger(__name__, default_level = "INFO")

@plac.annotations(
    bundle_path = ("path to new bundle",),
    root_path = ("instances root directory",),
    runs_extension = ("runs files extension",),
    )
def main(bundle_path, root_path, runs_extension):
    """Bundle together run and feature data."""

    cargo.enable_default_logging()

    # list relevant files
    features_extension = ".features.csv"
    runs_paths = map(os.path.abspath, cargo.files_under(root_path, "*{0}".format(runs_extension)))
    features_paths = map(os.path.abspath, cargo.files_under(root_path, "*{0}".format(features_extension)))

    # write the bundle
    os.mkdir(bundle_path)
    csv.field_size_limit(1000000000)

    logger.info("bundling run data from %i files", len(runs_paths))

    with cargo.openz(os.path.join(bundle_path, "all_runs.csv.gz"), "w") as out_file:
        out_writer = csv.writer(out_file)

        out_writer.writerow(["instance", "solver", "budget", "cost", "succeeded"])

        for runs_path in runs_paths:
            logger.info("reading %s", runs_path)

            instance_path = runs_path[:-len(runs_extension)]

            with open(runs_path) as in_file:
                in_reader = csv.reader(in_file)
                column_names = in_reader.next()

                assert column_names[:4] == ["solver", "budget", "cost", "succeeded"]

                for row in in_reader:
                    out_writer.writerow([instance_path] + row[:4])

    logger.info("bundling feature data from %i files", len(features_paths))

    with cargo.openz(os.path.join(bundle_path, "all_features.csv.gz"), "w") as out_file:
        out_writer = csv.writer(out_file)
        feature_names = None

        for features_path in features_paths:
            logger.info("reading %s", features_path)

            instance_path = features_path[:-len(features_extension)]

            with open(features_path) as in_file:
                in_reader = csv.reader(in_file)

                if feature_names is None:
                    feature_names = in_reader.next()

                    out_writer.writerow(["instance"] + feature_names)
                else:
                    column_names = in_reader.next()

                    assert feature_names == column_names

                for row in in_reader:
                    out_writer.writerow([instance_path] + row)

