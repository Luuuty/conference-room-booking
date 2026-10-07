from datetime import datetime, timedelta, timezone

import pytest
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from bookings.models import Booking
from rooms.models import Room

pytestmark = [pytest.mark.postgres, pytest.mark.django_db]


@pytest.fixture
def room():
    return Room.objects.create(name="Зал", floor=1, capacity=10)


def create_booking(room, start=10, end=11, **overrides):
    midnight = datetime(2026, 11, 1, tzinfo=timezone.utc)
    values = {
        "room": room,
        "full_name": "Тестовый участник",
        "email": "test@example.com",
        "start_at": midnight + timedelta(hours=start),
        "end_at": midnight + timedelta(hours=end),
    }
    values.update(overrides)
    return Booking.objects.create(**values)


def test_adjacent_bookings_allowed(room):
    create_booking(room)
    second = create_booking(room, start=11, end=12)
    second.full_clean()
    assert room.bookings.count() == 2


@pytest.mark.parametrize("start,end", [(10, 11), (10.5, 12), (9, 10.5), (9, 12)])
def test_active_overlap_rejected_by_database(room, start, end):
    create_booking(room)
    with pytest.raises(IntegrityError) as error, transaction.atomic():
        create_booking(room, start=start, end=end)
    assert error.value.__cause__.diag.constraint_name == "booking_no_active_overlap"


def test_cancelled_booking_does_not_block(room):
    create_booking(room, status=Booking.Status.CANCELLED)
    create_booking(room)
    assert room.bookings.count() == 2


def test_other_room_can_use_same_interval(room):
    create_booking(room)
    other = Room.objects.create(name="Другой зал", floor=1, capacity=10)
    create_booking(other)
    assert Booking.objects.count() == 2


def test_reactivation_conflict_rejected(room):
    cancelled = create_booking(room, status=Booking.Status.CANCELLED)
    create_booking(room)
    with pytest.raises(IntegrityError) as error, transaction.atomic():
        Booking.objects.filter(pk=cancelled.pk).update(status=Booking.Status.ACTIVE)
    assert error.value.__cause__.diag.constraint_name == "booking_no_active_overlap"


def test_room_with_bookings_is_protected(room):
    create_booking(room)
    with pytest.raises(ProtectedError):
        room.delete()
