import pytest

from rooms.models import Equipment, Room

pytestmark = [pytest.mark.postgres, pytest.mark.django_db]


def test_create_room():
    room = Room.objects.create(name="Зал", floor=2, capacity=12)
    room.refresh_from_db()
    assert room.name == "Зал"
    assert room.floor == 2
    assert room.capacity == 12
    assert room.is_active
    assert room.created_at and room.updated_at
    assert str(room) == "Зал (этаж 2)"


def test_create_equipment_and_cascade():
    room = Room.objects.create(name="Зал", floor=2, capacity=12)
    equipment = Equipment.objects.create(room=room, name="Проектор")
    equipment.refresh_from_db()
    assert room.equipment.get() == equipment
    assert equipment.created_at and equipment.updated_at
    assert str(equipment) == "Проектор"
    room.delete()
    assert not Equipment.objects.filter(pk=equipment.pk).exists()
