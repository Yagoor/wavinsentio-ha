"""Wavin Sentio sensors: outdoor temperature and per-room temperature/humidity."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from wavinsentio.wavinsentio import OutdoorTemperatureSensor, Room

from . import WavinSentioDataCoordinator, room_name
from .const import CONF_DEVICE_NAME, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up the Wavin Sentio sensor entities.

    Args:
        hass: Home Assistant instance.
        entry: Config entry for the integration.
        async_add_entities: Function to add entities asynchronously.

    """
    dataservice = hass.data[DOMAIN].get("coordinator"+entry.data[CONF_DEVICE_NAME])

    if not dataservice:
        return

    sentio = dataservice.get_device().lastConfig.sentio
    entities = [WavinSentioOutdoorTemperatureSensor(dataservice, outdoorTemperatureSensor)
                for outdoorTemperatureSensor in sentio.outdoorTemperatureSensors]
    for room in sentio.rooms:
        entities.append(WavinSentioRoomSensor(
            dataservice, room, "airTemperature", "Temperature",
            SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS))
        entities.append(WavinSentioRoomSensor(
            dataservice, room, "humidity", "Humidity",
            SensorDeviceClass.HUMIDITY, PERCENTAGE))

    async_add_entities(entities)


class WavinSentioRoomSensor(CoordinatorEntity, SensorEntity):
    """A measurement (temperature or humidity) of a room, on the room's device."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, dataservice: WavinSentioDataCoordinator, room: Room, field: str,
                 label: str, device_class: SensorDeviceClass, unit: str) -> None:
        """Initialize the sensor for the given Room attribute."""
        super().__init__(dataservice)
        self._room_id = room.id
        self._field = field
        self._attr_name = f"{room_name(room)} {label}"
        self._attr_unique_id = f"{room.id}-{field}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        # Same identifiers as the climate entity, so both live on the room's device.
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(room.id))},
            "name": room_name(room),
            "manufacturer": "Wavin",
            "model": "Sentio",
        }

    @property
    def native_value(self):
        """Return the current value from the latest coordinator data."""
        room = self.coordinator.get_room(self._room_id)
        return getattr(room, self._field) if room is not None else None


class WavinSentioOutdoorTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Outdoor Temperature Sensor."""

    def __init__(self, dataservice : WavinSentioDataCoordinator, outdoorTemperatureSensor: OutdoorTemperatureSensor) -> None:
        """Initialize the sensor."""
        super().__init__(dataservice)
        self._state = None
        self._dataservice = dataservice
        self._outdoorTemperatureSensor = outdoorTemperatureSensor

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Outdoor Temperature"

    @property
    def state(self):
        """Return the state of the sensor."""
        for outdoorTemperatureSensor in self._dataservice.get_device().lastConfig.sentio.outdoorTemperatureSensors:
            if outdoorTemperatureSensor.id == self._outdoorTemperatureSensor.id:
                self._state = outdoorTemperatureSensor.outdoorTemperature
        return self._state

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def device_class(self):
        """Return the device class for the sensor."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def unique_id(self):
        """Return the ID of this device."""
        return f"OutdoorTemperature-{self._outdoorTemperatureSensor.id}"

    @property
    def device_info(self):
        """Return device information for Home Assistant device registry."""
        return {
            "identifiers": {
                (DOMAIN, self.unique_id)
            },
            "name": self.name,
            "manufacturer": "Wavin",
            "model": "Sentio",
        }
