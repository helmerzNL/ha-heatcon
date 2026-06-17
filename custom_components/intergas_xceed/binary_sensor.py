"""Binary sensor platform for Intergas XCeed."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up the binary sensor platform."""
    coordinator: IntergasXceedDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        IntergasXceedBinarySensor(coordinator, entry, path)
        for path, value in iter_leaf_paths(coordinator.data)
        if isinstance(value, bool)
    )


class IntergasXceedBinarySensor(IntergasXceedCoordinatorEntity, BinarySensorEntity):
    """Representation of an Intergas XCeed binary sensor."""

    def __init__(
        self,
        coordinator: IntergasXceedDataUpdateCoordinator,
        entry: ConfigEntry,
        path: tuple[str, ...],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._path = path
        self._attr_name = path_to_name(path)
        self._attr_unique_id = f"{entry.unique_id or coordinator.api.host}_{path_to_object_id(path)}"

    @property
    def is_on(self) -> bool | None:
        """Return whether the entity is currently on."""
        value: Any = resolve_path_value(self.coordinator.data, self._path)
        return value if isinstance(value, bool) else None
