"""Shared entity helpers for Intergas XCeed."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Iterator
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import IntergasXceedDataUpdateCoordinator


class IntergasXceedCoordinatorEntity(CoordinatorEntity[IntergasXceedDataUpdateCoordinator]):
    """Base entity for the integration."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return metadata about the Intergas device."""
        system_information = self.coordinator.data.get("system_information", {})
        model = _first_value(
            system_information,
            ("model",),
            ("product",),
            ("device_type",),
            ("type",),
        )
        serial_number = _first_value(
            system_information,
            ("serial",),
            ("serialnumber",),
            ("serial_number",),
            ("mac",),
        )
        sw_version = _first_value(
            system_information,
            ("firmware",),
            ("firmware_version",),
            ("version",),
            ("swversion",),
        )

        identifier = serial_number or self.coordinator.api.host
        return DeviceInfo(
            identifiers={(DOMAIN, str(identifier))},
            configuration_url=f"http://{self.coordinator.api.host}",
            manufacturer=MANUFACTURER,
            model=str(model) if model else "XCeed",
            name=f"Intergas XCeed ({self.coordinator.api.host})",
            serial_number=str(serial_number) if serial_number else None,
            sw_version=str(sw_version) if sw_version else None,
        )


def _first_value(payload: dict[str, Any], *paths: tuple[str, ...]) -> Any | None:
    """Return the first available nested value for the provided paths."""
    for path in paths:
        value = _nested_value(payload, path)
        if value not in (None, ""):
            return value
    return None


def _nested_value(payload: dict[str, Any], path: tuple[str, ...]) -> Any | None:
    """Look up a nested value by path."""
    current: Any = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def iter_leaf_paths(payload: Mapping[str, Any]) -> list[tuple[tuple[str, ...], Any]]:
    """Return all scalar leaf values from a nested payload."""
    return list(_iter_leaf_paths(payload, ()))


def path_to_name(path: tuple[str, ...]) -> str:
    """Convert a payload path into a readable entity name."""
    return " ".join(segment.replace("_", " ").replace("-", " ") for segment in path).title()


def path_to_object_id(path: tuple[str, ...]) -> str:
    """Convert a payload path into a stable object id suffix."""
    return "_".join(segment.replace("-", "_").lower() for segment in path)


def resolve_path_value(payload: Any, path: tuple[str, ...]) -> Any | None:
    """Resolve a nested path against mappings and lists."""
    current: Any = payload
    for key in path:
        if isinstance(current, Mapping):
            if key not in current:
                return None
            current = current[key]
            continue
        if isinstance(current, list):
            try:
                current = current[int(key)]
            except (ValueError, IndexError):
                return None
            continue
        return None
    return current


def _iter_leaf_paths(
    value: Any,
    path: tuple[str, ...],
) -> Iterator[tuple[tuple[str, ...], Any]]:
    """Yield scalar leaf values from nested mappings and lists."""
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            if key.lower() in {"success", "message", "performance", "loginrejected"}:
                continue
            yield from _iter_leaf_paths(nested_value, (*path, str(key)))
        return

    if isinstance(value, list):
        for index, nested_value in enumerate(value):
            yield from _iter_leaf_paths(nested_value, (*path, str(index)))
        return

    if path:
        yield (path, value)
