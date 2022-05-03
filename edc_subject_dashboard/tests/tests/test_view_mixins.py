from dateutil.relativedelta import relativedelta
from django.test import TestCase
from edc_facility import import_holidays
from edc_locator.view_mixins import (
    SubjectLocatorViewMixin,
    SubjectLocatorViewMixinError,
)
from edc_registration.models import RegisteredSubject
from edc_utils import get_utcnow
from edc_visit_schedule import site_visit_schedules

from edc_subject_dashboard.view_mixins import (
    SubjectVisitViewMixin,
    SubjectVisitViewMixinError,
)

from ..models import (
    Appointment,
    BadSubjectVisit,
    OnScheduleOne,
    SubjectVisit,
    TestModel,
)
from ..visit_schedule import visit_schedule1


class DummyModelWrapper:
    def __init__(self, **kwargs):
        pass


class TestViewMixins(TestCase):
    def setUp(self):
        site_visit_schedules._registry = {}
        site_visit_schedules.register(visit_schedule=visit_schedule1)

        self.subject_identifier = "12345"

        onschedule_datetime = get_utcnow() - relativedelta(years=1)

        RegisteredSubject.objects.create(
            subject_identifier=self.subject_identifier,
            registration_datetime=onschedule_datetime,
        )

        OnScheduleOne.objects.create(
            subject_identifier=self.subject_identifier,
            onschedule_datetime=onschedule_datetime,
        )

        self.appointment = Appointment.objects.create(
            subject_identifier=self.subject_identifier,
            visit_code="1000",
            appt_datetime=onschedule_datetime + relativedelta(days=1),
            visit_schedule_name="visit_schedule1",
            schedule_name="schedule1",
        )
        self.subject_visit = SubjectVisit.objects.create(
            appointment=self.appointment, subject_identifier=self.subject_identifier
        )
        self.bad_subject_visit = BadSubjectVisit.objects.create(
            appointment=self.appointment, subject_identifier=self.subject_identifier
        )
        self.test_model = TestModel.objects.create(subject_visit=self.subject_visit)

    @classmethod
    def setUpTestData(cls):
        import_holidays()

    def test_subject_visit_missing_appointment(self):
        mixin = SubjectVisitViewMixin()
        self.assertRaises(SubjectVisitViewMixinError, mixin.get_context_data)

    def test_subject_visit_correct_relation(self):
        mixin = SubjectVisitViewMixin()
        mixin.appointment = self.appointment
        context = mixin.get_context_data()
        self.assertEqual(context.get("subject_visit"), self.subject_visit)

    def test_subject_visit_incorrect_relation(self):
        """Asserts raises if relation is not one to one."""

        class MySubjectVisitViewMixin(SubjectVisitViewMixin):
            visit_attr = "badsubjectvisit"

        mixin = MySubjectVisitViewMixin()
        self.assertRaises(SubjectVisitViewMixinError, mixin.get_context_data)

    def test_subject_locator_raises_on_bad_model(self):
        class MySubjectLocatorViewMixin(SubjectLocatorViewMixin):
            subject_locator_model_wrapper_cls = DummyModelWrapper
            subject_locator_model = "blah.blahblah"

        mixin = MySubjectLocatorViewMixin()
        self.assertRaises(SubjectLocatorViewMixinError, mixin.get_context_data)

    def test_subject_locator_raisesmissing_wrapper_cls(self):
        class MySubjectLocatorViewMixin(SubjectLocatorViewMixin):
            subject_locator_model = "edc_locator.subjectlocator"

        self.assertRaises(SubjectLocatorViewMixinError, MySubjectLocatorViewMixin)

    def test_subject_locator_ok(self):
        class MySubjectLocatorViewMixin(SubjectLocatorViewMixin):
            subject_locator_model_wrapper_cls = DummyModelWrapper
            subject_locator_model = "edc_locator.subjectlocator"

        mixin = MySubjectLocatorViewMixin()
        mixin.kwargs = {"subject_identifier": self.subject_identifier}
        try:
            mixin.get_context_data()
        except SubjectLocatorViewMixinError as e:
            self.fail(e)