from django.core.validators import MinValueValidator
from django.db import models


class Room(models.Model):
    name = models.CharField(max_length=200)
    floor = models.IntegerField()
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["floor", "name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1), name="room_capacity_positive"
            ),
        ]

    def __str__(self):
        return f"{self.name} (этаж {self.floor})"


class Equipment(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="equipment")
    name = models.CharField(max_length=200)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
