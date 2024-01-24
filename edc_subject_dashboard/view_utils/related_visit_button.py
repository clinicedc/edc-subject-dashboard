from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Type, TypeVar

from edc_appointment.constants import (
    CANCELLED_APPT,
    COMPLETE_APPT,
    INCOMPLETE_APPT,
    SKIPPED_APPT,
)
from edc_constants.constants import INCOMPLETE
from edc_pharmacy.constants import IN_PROGRESS_APPT

from .dashboard_model_button import DashboardModelButton
from .model_button import ADD, CHANGE, VIEW

if TYPE_CHECKING:
    from django.contrib.sites.models import Site
    from edc_appointment.models import Appointment
    from edc_visit_tracking.model_mixins import VisitModelMixin

    RelatedVisitModel = TypeVar("RelatedVisitModel", bound=VisitModelMixin)

__all__ = ["RelatedVisitButton"]


@dataclass
class RelatedVisitButton(DashboardModelButton):
    appointment: Appointment = None
    model_obj: RelatedVisitModel = None
    labels: tuple[str, str, str] = field(default=("Start", "Visit Report", "Visit Report"))
    model_cls: Type[RelatedVisitModel] = field(default=None)

    def __post_init__(self):
        pass

    @property
    def site(self) -> Site | None:
        """If model_obj is None, then Site should come from the
        CRFMetadata or RequisitionMetadata models.
        """
        return getattr(self.model_obj, "site", self.appointment.site)

    def color(self) -> str:
        """Shows as orange to direct user to edit the related visit
        following setting the appointment to in IN_PROGRESS_APPT.

        Note:
            In the background, setting an appointment to
            IN_PROGRESS_APPT updates the related visit
            document_status to INCOMPLETE. See also
            DocumentStatusModelMixin and AppointmentReasonUpdater.
        """
        color = self.colors[VIEW]
        if self.appointment.appt_status == IN_PROGRESS_APPT:
            if self.model_obj and self.model_obj.document_status == INCOMPLETE:
                color = self.colors[ADD]
            elif not self.model_obj:
                color = self.colors[ADD]
            else:
                color = self.colors[VIEW]  # default / grey
        elif self.appointment.appt_status in [COMPLETE_APPT, SKIPPED_APPT]:
            color = self.colors[CHANGE]
        return color

    @property
    def disabled(self) -> str:
        """Is only enabled if the related appointment is set to
        IN_PROGRESS_APPT.
        """
        disabled = "disabled"
        if self.appointment.appt_status == IN_PROGRESS_APPT and any(
            [self.perms.add, self.perms.change, self.perms.view]
        ):
            disabled = ""
        return disabled

    @property
    def label(self) -> str:
        label = super().label
        if self.appointment.appt_status == SKIPPED_APPT:
            label = "Skipped"
        elif self.appointment.appt_status == CANCELLED_APPT:
            label = "Cancelled"
        elif self.appointment.appt_status == COMPLETE_APPT:
            label = "Done"
        elif self.appointment.appt_status == INCOMPLETE_APPT:
            label = "Incomplete"
        elif self.appointment.appt_status == IN_PROGRESS_APPT:
            label = "Visit Report"
        return label

    @property
    def title(self):
        title = super().title
        if self.model_obj and self.model_obj.document_status == INCOMPLETE:
            title = "Click to review before continuing to forms."
        return title
