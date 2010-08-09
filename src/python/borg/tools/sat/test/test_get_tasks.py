"""
@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

from nose.tools import (
    assert_true,
    assert_equal,
    )

def assert_tasks_stored(session):
    """
    Verify that the tasks have been stored.
    """

    from borg.data import (
        TaskRow     as TR,
        TaskNameRow as TNR,
        )

    # we should have eight unique tasks
    assert_equal(session.query(TR).count(), 8)

    for i in xrange(8):
        for j in xrange(8):
            task_row =                                   \
                session                                  \
                .query(TNR)                               \
                .filter(TNR.name == "tasks/%i/%i.cnf" % (i, j)) \
                .filter(TNR.collection == "sat/")         \
                .first()

            assert_true(task_row is not None)
            assert_true(task_row.task is not None)

def make_cnf(literals):
    """
    Make arbitrary (incorrect, but well-formed) CNF text.
    """

    return "p cnf 2 6\n%s 0\n" % " ".join(str(i) for i in literals)

def test_get_tasks():
    """
    Test the tools.get_tasks script.
    """

    # scan a fake path
    from cargo.io import mkdtemp_scoped

    with mkdtemp_scoped() as sandbox_path:
        # populate a directory with tasks
        from os      import makedirs
        from os.path import join

        tasks_path = join(sandbox_path, "tasks")
        task_paths = []

        for i in xrange(8):
            tasks_i_path = join(tasks_path, "%i" % i)

            makedirs(tasks_i_path)

            for j in xrange(8):
                task_ij_path = join(tasks_i_path, "%i.cnf" % j)

                with open(task_ij_path, "w") as file:
                    file.write(make_cnf([j]))

        # invoke the script
        from subprocess import check_call
        from functools  import partial
        from cargo.io   import unset_all

        research_engine_url = "sqlite:///%s" % join(sandbox_path, "test.sqlite")

        with open("/dev/null", "w") as null_file:
            check_call(
                [
                    "python",
                    "-m",
                    "borg.tools.sat.get_tasks",
                    tasks_path,
                    sandbox_path,
                    "--collection",
                    "sat/",
                    "--research-database",
                    research_engine_url,
                    "--create-research-schema",
                    ],
                stdout     = null_file,
                stderr     = null_file,
                preexec_fn = partial(unset_all, "CARGO_FLAGS_EXTRA"),
                )

        # success?
        from sqlalchemy        import create_engine
        from cargo.sql.alchemy import (
            disposing,
            make_session,
            )

        research_engine = create_engine(research_engine_url)
        ResearchSession = make_session(bind = research_engine)

        with disposing(research_engine):
            with ResearchSession() as session:
                assert_tasks_stored(session)

