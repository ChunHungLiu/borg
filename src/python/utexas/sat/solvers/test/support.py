"""
@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

from uuid               import uuid4
from utexas.sat.solvers import SAT_Solver

task_uuids = [uuid4() for i in xrange(5)]

class FixedSolver(SAT_Solver):
    """
    A fake, fixed-result solver.
    """

    def __init__(self, satisfiable, certificate):
        """
        Initialize.
        """

        self.satisfiable = satisfiable
        self.certificate = certificate

    def solve(self, task, budget, random, environment):
        """
        Pretend to solve the task.
        """

        from utexas.sat.solvers import SAT_BareResult

        return \
            SAT_BareResult(
                self,
                task,
                budget,
                budget,
                self.satisfiable,
                self.certificate,
                )

def add_fake_foo_run(session, recyclable_trial_row, task_row, satisfiable):
    """
    Insert a fake run.
    """

    from utexas.data import (
        CPU_LimitedRunRow,
        SAT_RunAttemptRow,
        )

    run_row     = \
        CPU_LimitedRunRow(
            proc_elapsed = 8.0,
            cutoff       = 32.0,
            )
    attempt_row = \
        SAT_RunAttemptRow(
            task        = task_row,
            budget      = 32.0,
            cost        = 8.0,
            satisfiable = satisfiable,
            trials      = [recyclable_trial_row],
            run         = run_row,
            solver_name = "foo_solver",
            )

    if satisfiable:
        attempt_row.set_certificate([42])

    session.add(run_row)
    session.add(attempt_row)

def add_fake_bar_run_preed(session, recyclable_trial_row, task_row, satisfiable):
    """
    Insert a fake run.
    """

    from utexas.data import (
        CPU_LimitedRunRow,
        SAT_PreprocessingAttemptRow,
        )

    run_row           = \
        CPU_LimitedRunRow(
            proc_elapsed = 8.0,
            cutoff       = 32.0,
            )
    attempt_row       = \
        SAT_PreprocessingAttemptRow(
            task              = task_row,
            budget            = 32.0,
            cost              = 8.0,
            satisfiable       = satisfiable,
            trials            = [recyclable_trial_row],
            run               = run_row,
            preprocessor_name = "bar_preprocessor",
            preprocessed      = True,
            )

    if satisfiable:
        attempt_row.set_certificate([43])

    session.add(run_row)
    session.add(attempt_row)

def add_fake_bar_run_innered(session, recyclable_trial_row, task_row, satisfiable, preprocessed):
    """
    Insert a fake run.
    """

    from utexas.data import (
        CPU_LimitedRunRow,
        SAT_RunAttemptRow,
        SAT_PreprocessingAttemptRow,
        )

    run_row           = \
        CPU_LimitedRunRow(
            proc_elapsed = 8.0,
            cutoff       = 32.0,
            )
    inner_attempt_row = \
        SAT_RunAttemptRow(
            task        = None if preprocessed else task_row,
            run         = run_row,
            budget      = 32.0,
            cost        = 8.0,
            satisfiable = satisfiable,
            trials      = [recyclable_trial_row],
            solver_name = "foo_solver",
            )
    attempt_row       = \
        SAT_PreprocessingAttemptRow(
            task              = task_row,
            budget            = 32.0,
            cost              = 8.0,
            satisfiable       = satisfiable,
            trials            = [recyclable_trial_row],
            run               = run_row,
            preprocessor_name = "bar_preprocessor",
            inner_attempt     = inner_attempt_row,
            preprocessed      = preprocessed,
            )

    if satisfiable:
        attempt_row.set_certificate([43])
        inner_attempt_row.set_certificate([43])

    session.add(run_row)
    session.add(inner_attempt_row)
    session.add(attempt_row)

def add_fake_runs(session):
    """
    Insert standard test data into an empty database.
    """

    from utexas.data import (
        DatumBase,
        SAT_TaskRow,
        SAT_TrialRow,
        CPU_LimitedRunRow,
        SAT_RunAttemptRow,
        )

    # layout
    DatumBase.metadata.create_all(session.connection().engine)

    # add the recyclable-run trial
    recyclable_trial_row = SAT_TrialRow(uuid = SAT_TrialRow.RECYCLABLE_UUID)

    session.add(recyclable_trial_row)

    # add the task
    task_rows = [SAT_TaskRow(uuid = u) for u in task_uuids]

    session.add_all(task_rows)

    # add fake runs
    add_fake_foo_run(session, recyclable_trial_row, task_rows[0], True)
    add_fake_foo_run(session, recyclable_trial_row, task_rows[1], False)
    add_fake_foo_run(session, recyclable_trial_row, task_rows[2], None)
    add_fake_bar_run_preed(session, recyclable_trial_row, task_rows[0], True)
    add_fake_bar_run_preed(session, recyclable_trial_row, task_rows[1], False)
    add_fake_bar_run_innered(session, recyclable_trial_row, task_rows[2], False, True)
    add_fake_bar_run_innered(session, recyclable_trial_row, task_rows[3], True, True)
    add_fake_bar_run_innered(session, recyclable_trial_row, task_rows[4], True, False)

    session.commit()

class FakeSolverData(object):
    """
    Tests of the mock solver(s).
    """

    def set_up(self):
        """
        Prepare for a test.
        """

        from sqlalchemy        import create_engine
        from cargo.sql.alchemy import make_session

        self.engine  = create_engine("sqlite:///:memory:")
        self.Session = make_session(bind = self.engine)
        self.session = self.Session()

        add_fake_runs(self.session)

    def tear_down(self):
        """
        Clean up after a test.
        """

        self.session.close()
        self.engine.dispose()

