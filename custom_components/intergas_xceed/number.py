"""Number platform for Intergas XCeed comfort setpoints."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import IntergasXceedDataUpdateCoordinator, XceedRoom
from .entity import IntergasXceedEntity

DEFAULT_MIN_TEMP = 5.0
DEFAULT_MAX_TEMP = 35.0


@dataclass(frozen=True, kw_only=True)
class XceedSetpointDescription:
    """Describes a writable comfort setpoint of a room."""

    key: str
    label: str
    value_fn: Callable[[XceedRoom], float | None]


SETPOINTS: tuple[XceedSetpointDescription, ...] = (
    XceedSetpointDescription(
        key="day",
        label="Day setpoint",
        value_fn=lambda room: room.day_temperature,
    ),
    XceedSetpointDescription(
        key="day2",
        label="Day 2 setpoint",
        value_fn=lambda room: room.day2_temperature,
    ),
    XceedSetpointDescription(
        key="night",
        label="Night setpoint",
        value_fn=lambda room: room.night_temperature,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the setpoint number entities."""
    coordinator: IntergasXceedDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[IntergasXceedSetpointNumber] = []
    for room in coordinator.data.rooms:
        if room.is_dhw:
            continue
        for description in SETPOINTS:
            if description.value_fn(room) is None:
                continue
            entities.append(
                IntergasXceedSetpointNumber(coordinator, room.id, description)
            )
    async_add_entities(entities)


class IntergasXceedSetpointNumber(IntergasXceedEntity, NumberEntity):
    """A writable day/day2/night comfort setpoint for a heating zone."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: IntergasXceedDataUpdateCoordinator,
        room_id: int,
        description: XceedSetpointDescription,
    ) -> None:
        """Initialise the setpoint number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._room_id = room_id
        self._attr_unique_id = f"{self._serial}_setpoint_{description.key}_{room_id}"
        room = self._room
        room_name = room.name if room else f"Zone {room_id}"
        self._attr_name = f"{room_name} {description.label}"

    @property
    def _room(self) -> XceedRoom | None:
        """Return the backing room from the latest data."""
        for room in self.coordinator.data.rooms:
            if room.id == self._room_id:
                return room
        return None

    @property
    def available(self) -> bool:
        """Return True if the zone is present in the latest update."""
        return super().available and self._room is not None

    @property
    def native_min_value(self) -> float:
        """Return the minimum settable setpoint."""
        room = self._room
        if room and room.min_temperature is not None:
            return room.min_temperature
        return DEFAULT_MIN_TEMP

    @property
    def native_max_value(self) -> float:
        """Return the maximum settable setpoint."""
        room = self._room
        if room and room.max_temperature is not None:
            return room.max_temperature
        return DEFAULT_MAX_TEMP

    @property
    def native_value(self) -> float | None:
        """Return the current value of this setpoint."""
        room = self._room
        if room is None:
            return None
        return self.entity_description.value_fn(room)

    async def async_set_native_value(self, value: float) -> None:
        """Write a new value for this setpoint."""
        room = self._room
        if room is None:
            return
        day = room.day_temperature
        day2 = room.day2_temperature
        night = room.night_temperature
        if self.entity_description.key == "day":
            day = value
        elif self.entity_description.key == "day2":
            day2 = value
        else:
            night = value
        if day is None or night is None:
            return
        await self.coordinator.api.async_set_room_setpoints(
            self._room_id,
            room.name,
            day,
            day2,
            night,
        )
        await self.coordinator.async_request_refresh()
