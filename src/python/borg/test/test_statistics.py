"""@author: Bryan Silverthorn <bcs@cargo-cult.org>"""

import numpy
import scipy.stats
import scipy.special
import nose.tools
import cargo
import borg

def test_digamma():
    nose.tools.assert_almost_equal(borg.statistics.digamma(1e-2), scipy.special.digamma(1e-2))
    nose.tools.assert_almost_equal(borg.statistics.digamma(1e-1), scipy.special.digamma(1e-1))
    nose.tools.assert_almost_equal(borg.statistics.digamma(1e-0), scipy.special.digamma(1e-0))
    nose.tools.assert_almost_equal(borg.statistics.digamma(1e+1), scipy.special.digamma(1e+1))
    nose.tools.assert_almost_equal(borg.statistics.digamma(1e+2), scipy.special.digamma(1e+2))

def test_inverse_digamma():
    def assert_inverse_digamma_ok(x):
        v = borg.statistics.digamma(x)

        nose.tools.assert_almost_equal(borg.statistics.inverse_digamma(v), x)

    assert_inverse_digamma_ok(1e-2)
    assert_inverse_digamma_ok(1e-1)
    assert_inverse_digamma_ok(1e-0)
    assert_inverse_digamma_ok(1e+1)
    assert_inverse_digamma_ok(1e+2)

def test_gamma_log_pdf():
    def assert_ok(x):
        nose.tools.assert_almost_equal(
            borg.statistics.gamma_log_pdf(x, 1.1, 2.0),
            scipy.stats.gamma.logpdf(x, 1.1, scale = 2.0),
            )

    with cargo.numpy_errors(all = "raise"):
        for i in xrange(4):
            x = numpy.random.rand() * 10

            yield (assert_ok, x)

def test_dirichlet_estimate_map_simple():
    with cargo.numpy_errors(all = "raise"):
        a = 1e-2
        b = 1.0 - 1e-2

        vectors = numpy.array([[a, b]] * 16, numpy.double)
        alpha = borg.statistics.dirichlet_estimate_map(vectors, shape = 1.1, scale = 2.0)
        mean = alpha / numpy.sum(alpha)

        nose.tools.assert_true(alpha[0] < alpha[1])
        nose.tools.assert_true(numpy.all(alpha > 0.0))
        nose.tools.assert_almost_equal(mean[0], a, places = 1)
        nose.tools.assert_almost_equal(mean[1], b, places = 1)

def test_dirichlet_estimate_map_zeros():
    with cargo.numpy_errors(all = "raise"):
        a = 0.0
        b = 1.0

        vectors = numpy.array([[a, b]] * 16, numpy.double)
        alpha = borg.statistics.dirichlet_estimate_map(vectors)
        mean = alpha / numpy.sum(alpha)

        nose.tools.assert_true(alpha[0] < alpha[1])
        nose.tools.assert_almost_equal(mean[0], a, places = 1)
        nose.tools.assert_almost_equal(mean[1], b, places = 1)

def test_dirichlet_estimate_map_disjoint():
    with cargo.numpy_errors(all = "raise"):
        a = 0.0
        b = 1.0

        vectors = numpy.array([[a, b]] * 16 + [[b, a]] * 16, numpy.double)
        alpha = borg.statistics.dirichlet_estimate_map(vectors, shape = 30, scale = 2)

        nose.tools.assert_almost_equal(alpha[0], alpha[1])

def test_dirichlet_estimate_map_random():
    def assert_ok(alpha):
        vectors = numpy.random.dirichlet(alpha, 65536)
        estimate = borg.statistics.dirichlet_estimate_map(vectors)

        nose.tools.assert_almost_equal(estimate[0], alpha[0], places = 1)
        nose.tools.assert_almost_equal(estimate[1], alpha[1], places = 1)

    with cargo.numpy_errors(all = "raise"):
        for i in xrange(8):
            alpha = numpy.random.dirichlet(numpy.ones(2)) + 1e-1

            yield (assert_ok, alpha.tolist())

def test_dcm_estimate_ml_simple():
    counts = numpy.array([[4, 4], [4, 4]], numpy.intc)
    alpha = borg.statistics.dcm_estimate_ml(counts)

    nose.tools.assert_almost_equal(alpha[0], alpha[1])

def test_dcm_estimate_ml_random():
    def assert_ok(alpha):
        vectors = numpy.random.dirichlet(alpha, 65536)
        counts = numpy.empty_like(vectors)

        for n in xrange(vectors.shape[0]):
            counts[n] = numpy.random.multinomial(8, vectors[n])

        estimate = borg.statistics.dcm_estimate_ml(counts)

        nose.tools.assert_almost_equal(estimate[0], alpha[0], places = 1)
        nose.tools.assert_almost_equal(estimate[1], alpha[1], places = 1)

    with cargo.numpy_errors(all = "raise"):
        for i in xrange(8):
            alpha = numpy.random.dirichlet(numpy.ones(2)) + numpy.random.rand() + 1e-1

            yield (assert_ok, alpha.tolist())

