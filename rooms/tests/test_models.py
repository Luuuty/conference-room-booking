import pytest
from django.core.exceptions import ValidationError

from rooms.models import Room


@pytest.mark.parametrize("capacity", [0, -1])
def test_capacity_must_be_positive(capacity):
    room = Room(name="Зал", floor=1, capacity=capacity)
    with pytest.raises(ValidationError) as error:
        room.full_clean(validate_constraints=False)
    assert "capacity" in error.value.message_dict
