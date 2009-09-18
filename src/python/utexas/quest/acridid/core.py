"""
utexas/quest/acridid/core.py

Common acridid code.

@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

import os.path
import socket
import logging

from uuid import uuid4
from datetime import timedelta
from itertools import chain
from sqlalchemy import (
    Column,
    Binary,
    String,
    Integer,
    Boolean,
    Interval,
    ForeignKey,
    )
from sqlalchemy.orm import relation
from sqlalchemy.orm.exc import NoResultFound
from cargo.io import (
    hash_file,
    files_under,
    )
from cargo.log import get_logger
from cargo.sql.alchemy import (
    SQL_Base,
    SQL_UUID,
    SQL_JSON,
    SQL_Session,
    UTC_DateTime,
    )
from cargo.temporal import utc_now

log = get_logger(__name__, level = None)

class SAT_Task(SQL_Base):
    """
    One satisfiability task in DIMACS CNF format.
    """

    __tablename__ = "sat_tasks"

    uuid = Column(SQL_UUID, primary_key = True, default = uuid4)
    name = Column(String)
    hash = Column(Binary(length = 64))
    path = Column(String)

class SAT_SolverDescription(SQL_Base):
    """
    Information about a SAT solver.
    """

    __tablename__ = "sat_solvers"

    name = Column(String, primary_key = True)
    path = Column(String)

class SAT_SolverConfiguration(SQL_Base):
    """
    Configuration of a SAT solver.
    """

    __tablename__ = "sat_solver_configurations"

    uuid        = Column(SQL_UUID, primary_key = True, default = uuid4)
    name        = Column(String)
    solver_name = Column(String, ForeignKey("sat_solvers.name"))

    __mapper_args__ = {"polymorphic_on": solver_name}

class ArgoSAT_Configuration(SAT_SolverConfiguration):
    """
    Configuration of ArgoSAT.
    """

    __tablename__ = "argosat_configurations"
    __mapper_args__ = {"polymorphic_identity": "argosat"}

    uuid                = Column(SQL_UUID, ForeignKey("sat_solver_configurations.uuid"), primary_key = True)
    variable_selection  = Column(SQL_JSON)
    polarity_selection  = Column(SQL_JSON)
    restart_scheduling  = Column(SQL_JSON)

    @property
    def argv(self):
        arguments = [] 

        if self.variable_selection:
            arguments.append("--variable_selection_strategy")
            arguments.extend(self.variable_selection)

        if self.polarity_selection:
            arguments.append("--literal_polarity_selection_strategy")
            arguments.extend(self.polarity_selection)

        if self.restart_scheduling:
            arguments.append("--restart_strategy")
            arguments.extend(self.restart_scheduling)

        return tuple(arguments)

class SAT_SolverRun(SQL_Base):
    """
    Information about one run of a solver on a SAT task.
    """

    __tablename__ = "sat_solver_runs"

    uuid                = Column(SQL_UUID, primary_key = True, default = uuid4)
    task_uuid           = Column(SQL_UUID, ForeignKey("sat_tasks.uuid"), nullable = False)
    solver_name         = Column(String, ForeignKey("sat_solvers.name"), nullable = False)
    configuration_uuid  = Column(SQL_UUID, ForeignKey("sat_solver_configurations.uuid"), nullable = False)
    outcome             = Column(Boolean)
    started             = Column(UTC_DateTime)
    elapsed             = Column(Interval)
    censored            = Column(Boolean)
    fqdn                = Column(String)
    seed                = Column(Integer)

    task          = relation(SAT_Task)
    solver        = relation(SAT_SolverDescription)
    configuration = relation(SAT_SolverConfiguration)

    @staticmethod
    def starting_now(*args, **kwargs):
        """
        Return a partially-initialized run starting now.
        """

        assert "started" not in kwargs
        assert "fqdn" not in kwargs

        run = SAT_SolverRun(*args, **kwargs)

        run.started = utc_now()
        run.fqdn    = socket.getfqdn()

        return run

