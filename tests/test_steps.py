"""
Tests for steps with allure-adaptor

Created on Nov 3, 2013

@author: pupssman
"""

import time

from hamcrest import assert_that, has_property, has_entry, has_properties, contains
from hamcrest.library.number.ordering_comparison import greater_than_or_equal_to, \
    less_than_or_equal_to
from hamcrest.core.core.allof import all_of
from tests.conftest import has_float
from allure.constants import Status
import pytest


def step_with(name, start, stop, status):
    return has_properties(name=name,
                          attrib=all_of(
                                        has_entry('start', has_float(greater_than_or_equal_to(start))),
                                        has_entry('stop', has_float(less_than_or_equal_to(stop))),
                                        has_entry('status', status)))


@pytest.fixture()
def timed_report_for(report_for):
    def impl(*a, **kw):
        start = time.time() * 1000
        report = report_for(*a, **kw)
        stop = time.time() * 1000

        return report, start, stop

    return impl


@pytest.mark.parametrize('status,expr', [(Status.PASSED, 'assert True'),
                                           (Status.FAILED, 'assert False'),
                                           (Status.SKIPPED, 'pytest.skip("foo")')])
def test_one_step(timed_report_for, status, expr):
    report, start, stop = timed_report_for("""
    import pytest
    def test_ololo_pewpew():
        with pytest.allure.step(title='my_fancy_step'):
            %s
    """ % expr)

    assert_that(report.findall('.//test-case/steps/step'), contains(step_with(name='my_fancy_step',
                                                                              start=start,
                                                                              stop=stop,
                                                                              status=status)))


def test_two_steps(timed_report_for):
    report, start, stop = timed_report_for("""
    import pytest
    def test_ololo_pewpew():
        with pytest.allure.step(title='step_1'):
            assert True

        with pytest.allure.step(title='step_2'):
            assert False
    """)

    assert_that(report.findall('.//test-case/steps/step'), contains(step_with('step_1', start, stop, Status.PASSED),
                                                          step_with('step_2', start, stop, Status.FAILED)))


def test_fixture_step(timed_report_for):
    report, start, stop = timed_report_for("""
    import pytest

    @pytest.fixture
    def afixture():
        with pytest.allure.step(title='fixture'):
            return 1

    def test_ololo_pewpew(afixture):
        assert afixture
    """)

    assert_that(report.findall('.//test-case/steps/step'), contains(step_with('fixture', start, stop, Status.PASSED)))


def test_nested_steps(timed_report_for):
    report, start, stop = timed_report_for("""
    import pytest
    def test_ololo_pewpew():
        with pytest.allure.step(title='outer'):
            with pytest.allure.step(title='inner'):
                assert False

    """)

    assert_that(report.findall('.//test-case/steps/step'), contains(all_of(step_with('outer', start, stop, Status.FAILED),
                                                                           has_property('steps',
                                                                                        has_property('step',
                                                                                                     step_with('inner', start, stop, Status.FAILED))))))


def test_step_attach(timed_report_for):
    report, start, stop = timed_report_for("""
    import pytest
    def test_ololo_pewpew():
        with pytest.allure.step(title='withattach'):
            pytest.allure.attach('myattach', 'abcdef')
    """)

    assert_that(report.findall('.//test-case/steps/step'), contains(all_of(step_with('withattach', start, stop, Status.PASSED),
                                                                           has_property('attachments',
                                                                                        has_property('attachment',
                                                                                                     has_entry('title', 'myattach'))))))


@pytest.mark.parametrize('package', ['pytest.allure', 'allure'])
def test_step_function_decorator(timed_report_for, package):
    report, start, stop = timed_report_for("""
    import pytest
    import allure

    @%s.step('step_foo')
    def foo(bar):
        return bar

    def test_ololo_pewpew():
        assert foo(123)
    """ % package)

    assert_that(report.findall('.//test-case/steps/step'), contains(step_with('step_foo', start, stop, Status.PASSED)))


@pytest.mark.parametrize('statement, expected_name', [('("ololo")', 'ololo'), ('', 'foo')])
def test_step_function_default_name(timed_report_for, statement, expected_name):
    report, start, stop = timed_report_for("""
    import pytest
    import allure

    @allure.step%s
    def foo(bar):
        return bar

    def test_ololo_pewpew():
        assert foo(123)
    """ % statement)

    assert_that(report.findall('.//test-case/steps/step'), contains(step_with(expected_name, start, stop, Status.PASSED)))


def test_step_fixture_decorator(timed_report_for):
    report, start, stop = timed_report_for("""
    import pytest

    @pytest.allure.step('fixture_step_foo')
    @pytest.fixture()
    def foo():
        return 123

    def test_ololo_pewpew(foo):
        assert foo
    """)

    assert_that(report.findall('.//test-case/steps/step'), contains(step_with('fixture_step_foo', start, stop, Status.PASSED)))


def test_step_fixture_method(timed_report_for):
    report, start, stop = timed_report_for("""
    import pytest

    class MyImpl:
        def __init__(self):
            pass

        @pytest.allure.step('fixture_step_bar')
        def bar(self, x):
            return x

    @pytest.fixture()
    def foo():
        return MyImpl()

    def test_ololo_pewpew(foo):
        assert foo.bar(5) == 5
    """)

    assert_that(report.findall('.//test-case/steps/step'), contains(step_with('fixture_step_bar', start, stop, Status.PASSED)))
