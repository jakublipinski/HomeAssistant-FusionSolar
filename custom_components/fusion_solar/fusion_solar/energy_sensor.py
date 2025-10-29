import logging
import math
from datetime import timedelta, time

from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy

from .const import ATTR_TOTAL_LIFETIME_ENERGY, ATTR_REALTIME_POWER, ATTR_STATION_REAL_KPI_TOTAL_LIFETIME_ENERGY

_LOGGER = logging.getLogger(__name__)


class FusionSolarEnergySensor(CoordinatorEntity, SensorEntity):
    """Base class for all FusionSolarEnergySensor sensors."""

    def __init__(
            self,
            coordinator,
            unique_id,
            name,
            attribute,
            data_name,
            device_info=None
    ):
        """Initialize the entity"""
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._name = name
        self._attribute = attribute
        self._data_name = data_name
        self._device_info = device_info

    @property
    def device_class(self) -> str:
        return SensorDeviceClass.ENERGY

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def native_value(self) -> float:
        import random
        _LOGGER.error(f'FUSION native value {random.random()}')
        # It seems like Huawei Fusion Solar returns some invalid data for the cumulativeEnergy just before midnight.
        # So we update the value only if it's increasing
        if self._attribute in [ATTR_STATION_REAL_KPI_TOTAL_LIFETIME_ENERGY, ATTR_TOTAL_LIFETIME_ENERGY]:
            # Grab the current data
            entity = self.hass.states.get(self.entity_id)
            _LOGGER.error(f'FUSION entity: {entity} {random.random()}')  
            if entity is not None:
                new_value = self.get_float_value_from_coordinator(self._attribute)
                _LOGGER.error(f'FUSION try new value1: {new_value} {random.random()}')  
                try:
                    current_value = float(entity.state)
                except ValueError:
                    _LOGGER.error(f'{self.entity_id}: not available, no check for decrease. {random.random()}')
                    current_value = None
                if current_value is not None and new_value is not None:
                    current_time = dt_util.now().time()
                    start_quiet = time(22, 0)
                    end_quiet = time(3, 0)
                    if new_value < current_value or start_quiet <= current_time or current_time < end_quiet:
                        _LOGGER.error(
                            f'{self.entity_id}: New value ({new_value}) is lower than current value ({current_value}) or in quite time. '
                            f'Keeping current value to prevent decrease.'
                        )
                        # Return the current value if the new value
                        return current_value
                        
        try:
            new_value = self.get_float_value_from_coordinator(self._attribute)
            _LOGGER.error(f'FUSION try new value: {new_value} {random.random()}')  
            return new_value
        except FusionSolarEnergySensorException as e:
            import random
            _LOGGER.error(f'FUSION exception {random.random()}')
            _LOGGER.error(e)
            return None

    @property
    def native_unit_of_measurement(self) -> str:
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def state_class(self) -> str:
        return SensorStateClass.TOTAL_INCREASING

    @property
    def device_info(self) -> dict:
        return self._device_info

    def is_producing_at_the_moment(self) -> bool:
        try:
            realtime_power = self.get_float_value_from_coordinator(ATTR_REALTIME_POWER)
            return not math.isclose(realtime_power, 0, abs_tol=0.001)
        except FusionSolarEnergySensorException as e:
            _LOGGER.info(e)
            return False

    def get_float_value_from_coordinator(self, attribute_name: str) -> float:
        if self.coordinator.data is False:
            raise FusionSolarEnergySensorException('Coordinator data is False')
        if self._data_name not in self.coordinator.data:
            raise FusionSolarEnergySensorException(f'Attribute {self._data_name} not in coordinator data')
        if self._attribute not in self.coordinator.data[self._data_name]:
            raise FusionSolarEnergySensorException(f'Attribute {attribute_name} not in coordinator data')

        if self.coordinator.data[self._data_name][attribute_name] is None:
            raise FusionSolarEnergySensorException(f'Attribute {attribute_name} has value None')
        elif self.coordinator.data[self._data_name][attribute_name] == 'N/A':
            raise FusionSolarEnergySensorException(f'Attribute {attribute_name} has value N/A')

        try:
            return float(self.coordinator.data[self._data_name][attribute_name])
        except ValueError:
            raise FusionSolarEnergySensorException(
                f'Attribute {self._attribute} has value {self.coordinator.data[self._data_name][attribute_name]} which is not a float')


class FusionSolarEnergySensorTotalCurrentDay(FusionSolarEnergySensor):
    pass


class FusionSolarEnergySensorTotalCurrentMonth(FusionSolarEnergySensor):
    pass


class FusionSolarEnergySensorTotalCurrentYear(FusionSolarEnergySensor):
    pass


class FusionSolarEnergySensorTotalLifetime(FusionSolarEnergySensor):
    pass


class FusionSolarEnergySensorException(Exception):
    pass
