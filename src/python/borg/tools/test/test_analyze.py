"""
@author: Bryan Silverthorn <bcs@cargo-cult.org>
"""

def populate_database(session):
    """
    Populate the database used for these tests.
    """

    from borg       import get_support_path
    from borg.data  import (
        DatumBase,
        FileTaskRow as FTR,
        )
    from borg.tasks import (
        builtin_domains,
        get_task_file_hash,
        )

    file_hash = get_task_file_hash(get_support_path("s57-100.cnf"), builtin_domains["sat"])
    task_row  = FTR(hash = buffer(file_hash))

    DatumBase.metadata.create_all(session.connection())

    session.add(task_row)
    session.commit()

def assert_instance_analyzed(session):
    """
    Assert that the instance has been analyzed.
    """

    from nose.tools import assert_equal
    from borg.data  import TaskFeatureRow as TFR

    assert_equal(session.query(TFR).count(), 1)

def test_analyze_instance():
    """
    Test the analyze_instance tool.
    """

    from cargo.io import mkdtemp_scoped

    with mkdtemp_scoped() as box_path:
        # populate the test database
        from os.path           import join
        from sqlalchemy        import create_engine
        from cargo.sql.alchemy import (
            disposing,
            make_session,
            )

        engine_url = "sqlite:///%s" % join(box_path, "test.sqlite")
        engine     = create_engine(engine_url)
        Session    = make_session(bind = engine)

        with disposing(engine):
            with Session() as session:
                populate_database(session)

        # invoke the script
        from functools  import partial
        from subprocess import CalledProcessError
        from cargo.io   import (
            unset_all,
            check_call_capturing,
            )
        from borg       import get_support_path

        try:
            check_call_capturing(
                [
                    "python",
                    "-m",
                    "borg.tools.analyze_instance",
                    "--research-database",
                    engine_url,
                    "--commit",
                    "sat",
                    get_support_path("s57-100.cnf"),
                    ],
                preexec_fn = partial(unset_all, "CARGO_FLAGS_EXTRA_FILE"),
                )
        except CalledProcessError, error:
            print error.stdout
            print error.stderr

            raise

        # success?
        with disposing(engine):
            with Session() as session:
                assert_instance_analyzed(session)

