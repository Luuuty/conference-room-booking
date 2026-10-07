from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import (
    DateTimeRangeField,
    RangeBoundary,
    RangeOperators,
)
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Booking(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активна"
        CANCELLED = "cancelled", "Отменена"

    room = models.ForeignKey(
        "rooms.Room", on_delete=models.PROTECT, related_name="bookings"
    )
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField()
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    participants_count = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=9, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_at", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_at__gt=models.F("start_at")),
                name="booking_end_after_start",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(participants_count__isnull=True)
                    | models.Q(participants_count__gte=1)
                ),
                name="booking_participants_positive",
            ),
            ExclusionConstraint(
                name="booking_no_active_overlap",
                expressions=[
                    ("room", RangeOperators.EQUAL),
                    (
                        models.Func(
                            "start_at",
                            "end_at",
                            RangeBoundary(),
                            function="TSTZRANGE",
                            output_field=DateTimeRangeField(),
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                ],
                condition=models.Q(status="active"),
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.start_at is not None and self.end_at is not None:
            if self.end_at <= self.start_at:
                errors["end_at"] = "Окончание должно быть позже начала."

        if self.participants_count is not None and self.participants_count <= 0:
            errors["participants_count"] = (
                "Количество участников должно быть больше нуля."
            )

        # Missing/invalid foreign keys are handled by full_clean() field validation.
        try:
            room = self.room
        except ObjectDoesNotExist:
            room = None

        if room is not None:
            if not room.is_active:
                errors["room"] = "Нельзя бронировать неактивный зал."
            if (
                self.participants_count is not None
                and room.capacity is not None
                and self.participants_count > room.capacity
            ):
                errors["participants_count"] = (
                    "Количество участников превышает вместимость зала."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.full_name}: {self.room}, {self.start_at} — {self.end_at}"
