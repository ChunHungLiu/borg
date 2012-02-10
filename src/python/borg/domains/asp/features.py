"""@author: Bryan Silverthorn <bcs@cargo-cult.org>"""

import resource
import borg

logger = borg.get_logger(__name__, default_level = "INFO")

def normalized_claspre_names(raw_names):
    """Convert names from claspre to "absolute" names."""

    parent = None
    names = []

    for raw_name in raw_names:
        if raw_name.startswith("_"):
            assert parent is not None

            names.append(parent + raw_name)
        elif len(raw_name) > 0:
            names.append(raw_name)

            parent = raw_name

    return names

def parse_claspre_value(raw_value):
    """Convert values from claspre to floats."""

    special = {
        "No": -1.0,
        "Yes": 1.0,
        "NA": 0.0,
        }

    value = special.get(raw_value)

    if value is None:
        return float(raw_value)
    else:
        return value

def get_features_for(asp_path, claspre_path):
    """Invoke claspre to compute features of an ASP instance."""

    previous_utime = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime

    # get feature names
    (names_out, _) = \
        borg.util.check_call_capturing([
            claspre_path,
            "--list-features",
            "--file",
            asp_path,
            ])
    (dynamic_names_out, static_names_out) = names_out.splitlines()
    dynamic_names = normalized_claspre_names(dynamic_names_out.split(","))
    static_names = normalized_claspre_names(static_names_out.split(","))

    # compute feature values
    (values_out, _, _) = \
        borg.util.call_capturing([
            claspre_path,
            "--rand-prob=10,30",
            "--search-limit=300,10",
            "--features=C1",
            "--file",
            asp_path,
            ])
    values_per = [map(parse_claspre_value, l.split(",")) for l in values_out.strip().splitlines()]

    # pull them together
    names = []
    values = []

    for (i, dynamic_values) in enumerate(values_per[:-1]):
        names += map("restart{0}-{{0}}".format(i).format, dynamic_names)
        values += dynamic_values

    names += static_names
    values += values_per[-1]

    # ...
    cost = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime - previous_utime

    borg.get_accountant().charge_cpu(cost)

    logger.info("collected features of %s in %.2fs", asp_path, cost)

    assert len(names) == len(values)

    return (names, values)

