from datetime import datetime, timedelta, timezone

import pytest
from django.core.exceptions import ValidationError

from bookings.models import Booking
from rooms.models import Room


@pytest.fixture
def booking():
    start = datetime(2026, 11, 1, 10, tzinfo=timezone.utc)
    return Booking(
        room=Room(name="Переговорная", floor=2, capacity=10),
        full_name="Тестовый участник",
        email="test@example.com",
        start_at=start,
        end_at=start + timedelta(hours=1),
    )


@pytest.mark.parametrize("minutes", [0, -30])
def test_end_must_be_after_start(booking, minutes):
    booking.end_at = booking.start_at + timedelta(minutes=minutes)
    with pytest.raises(ValidationError) as error:
        booking.clean()
    assert "end_at" in error.value.message_dict


def test_inactive_room_is_rejected(booking):
    booking.room.is_active = False
    with pytest.raises(ValidationError) as error:
        booking.clean()
    assert "room" in error.value.message_dict


@pytest.mark.parametrize("participants", [0, -1, 11])
def test_invalid_participants_are_rejected(booking, participants):
    booking.participants_count = participants
    with pytest.raises(ValidationError) as error:
        booking.clean()
    assert "participants_count" in error.value.message_dict


@pytest.mark.parametrize("participants", [None, 1, 10])
def test_valid_participants(booking, participants):
    booking.participants_count = participants
    booking.clean()


def test_missing_fields_do_not_crash_clean():
    Booking().clean()
