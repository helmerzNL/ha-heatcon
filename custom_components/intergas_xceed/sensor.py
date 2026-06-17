"""Sensor platform for Intergas XCeed."""

from __future__ import annotations

from numbers import Number
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import IntergasXceedDataUpdateCoordinator
from .entity import (
    IntergasXceedCoordinatorEntity,
    iter_leaf_paths,
    path_to_name,
    path_to_object_id,
    resolve_path_value,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: IntergasXceedDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        IntergasXceedSensor(coordinator, entry, path)
        for path, value in iter_leaf_paths(coordinator.data)
        if _is_sensor_value(value)
    )


class IntergasXceedSensor(IntergasXceedCoordinatorEntity, SensorEntity):
    """Representation of an Intergas XCeed sensor."""

    def __init__(
        self,
        coordinator: IntergasXceedDataUpdateCoordinator,
        entry: ConfigEntry,
        path: tuple[str, ...],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._path = path
        self._attr_name = path_to_name(path)
        self._attr_unique_id = f"{entry.unique_id or coordinator.api.host}_{path_to_object_id(path)}"

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        return resolve_path_value(self.coordinator.data, self._path)


def _is_sensor_value(value: Any) -> bool:
    """Return True if the payload value should be exposed as a sensor."""
    if value is None or isinstance(value, bool):
        return False
    return isinstance(value, (str, Number))
