"""@author: Bryan Silverthorn <bcs@cargo-cult.org>"""

import re
import itertools
import cargo
import borg

logger = cargo.get_logger(__name__)

def basic_command(relative):
    """Prepare a basic competition solver command."""

    return ["{{root}}/{0}".format(relative), "{task}", "{seed}"]

smallint_commands = {
    "pbct-0.1.2-linear": ["{root}/pbct-0.1.2-linux32", "--model", "{task}"],
    "bsolo_pb10-l1": ["{root}/bsolo_pb10", "-t1000000", "-m2048", "-l1", "{task}"],
    "bsolo_pb10-l2": ["{root}/bsolo_pb10", "-t1000000", "-m2048", "-l2", "{task}"],
    "bsolo_pb10-l3": ["{root}/bsolo_pb10", "-t1000000", "-m2048", "-l3", "{task}"],
    "wbo1.4a": ["{root}/wbo1.4a", "-time-limit=1000000", "-file-format=opb", "{task}"],
    "wbo1.4b-fixed": ["{root}/wbo1.4b-fixed", "-time-limit=1000000", "-file-format=opb", "{task}"],
    "clasp-1.3.7": ["{root}/clasp-1.3.7/clasp-1.3.7-x86-linux", "--seed={seed}", "{task}"],
    "sat4j-pb-v20101225": [
        "java",
        "-server",
        "-jar",
        "{root}/sat4j-pb-v20101225/sat4j-pb.jar",
        "{task}",
        ],
    "sat4j-pb-v20101225-cutting": [
        "java",
        "-server",
        "-jar",
        "{root}/sat4j-pb-v20101225/sat4j-pb.jar",
        "CuttingPlanes",
        "{task}",
        ],
    }
#bigint_commands = {
    #"pbct-0.1.2-linear": smallint_commands["pbct-0.1.2-linear"],
    #"sat4j-pb-v20101225": smallint_commands["sat4j-pb-v20101225"],
    #"sat4j-pb-v20101225-cutting": smallint_commands["sat4j-pb-v20101225-cutting"],
    #}
commands = smallint_commands

def parse_pb_output(stdout):
    """Parse a solver's standard competition-format output."""

    match = re.search(r"^s +([a-zA-Z ]+) *\r?$", stdout, re.M)

    if match:
        (answer_type,) = match.groups()
        answer_type = answer_type.strip().upper()

        if answer_type in ("SATISFIABLE", "OPTIMUM FOUND"):
            certificate = []

            for line in re.findall(r"^v ([ x\-0-9]*) *\r?$", stdout, re.M):
                certificate.extend(line.split())

            if len(certificate) == 0:
                return None
        elif answer_type == "UNSATISFIABLE":
            certificate = None
        else:
            return None

        return (answer_type, certificate)

    #logger.warning("NO ANSWER FOUND IN:\n%s", stdout)

    return None

def basic_solver(name, command):
    """Return a basic competition solver callable."""

    from borg.solvers.common import MonitoredSolver

    # XXX does this really need to support pickling?
    return cargo.curry(MonitoredSolver, parse_pb_output, command)

named = dict(zip(commands, itertools.starmap(basic_solver, commands.items())))
