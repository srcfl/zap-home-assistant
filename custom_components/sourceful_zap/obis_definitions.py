"""OBIS mappings."""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (UnitOfElectricCurrent,
                                 UnitOfElectricPotential, UnitOfEnergy,
                                 UnitOfPower, UnitOfReactiveEnergy,
                                 UnitOfReactivePower)

SENSOR_DEFINITIONS = {
    "1-0:1.8.0": {
        "name": "Total Energy Import",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:transmission-tower-import",
    },
    "1-0:2.8.0": {
        "name": "Total Energy Export",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:transmission-tower-export",
    },
    "1-0:1.7.0": {
        "name": "Current Power Import",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "1-0:2.7.0": {
        "name": "Current Power Export",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "1-0:3.8.0": {
        "name": "Total Reactive Energy Import",
        "unit": UnitOfReactiveEnergy.KILO_VOLT_AMPERE_REACTIVE_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:sine-wave",
    },
    "1-0:4.8.0": {
        "name": "Total Reactive Energy Export",
        "unit": UnitOfReactiveEnergy.KILO_VOLT_AMPERE_REACTIVE_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:sine-wave",
    },
    "1-0:3.7.0": {
        "name": "Current Reactive Power Import",
        "unit": UnitOfReactivePower.KILO_VOLT_AMPERE_REACTIVE,
        "device_class": SensorDeviceClass.REACTIVE_POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "1-0:4.7.0": {
        "name": "Current Reactive Power Export",
        "unit": UnitOfReactivePower.KILO_VOLT_AMPERE_REACTIVE,
        "device_class": SensorDeviceClass.REACTIVE_POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    # Phase voltages
    "1-0:32.7.0": {
        "name": "Voltage L1",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "1-0:52.7.0": {
        "name": "Voltage L2",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "1-0:72.7.0": {
        "name": "Voltage L3",
        "unit": UnitOfElectricPotential.VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    # Phase currents
    "1-0:31.7.0": {
        "name": "Current L1",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-ac",
    },
    "1-0:51.7.0": {
        "name": "Current L2",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-ac",
    },
    "1-0:71.7.0": {
        "name": "Current L3",
        "unit": UnitOfElectricCurrent.AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:current-ac",
    },
    # Phase power import
    "1-0:21.7.0": {
        "name": "Power L1 Import",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "1-0:41.7.0": {
        "name": "Power L2 Import",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    "1-0:61.7.0": {
        "name": "Power L3 Import",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:flash",
    },
    # Phase power export
    "1-0:22.7.0": {
        "name": "Power L1 Export",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "1-0:42.7.0": {
        "name": "Power L2 Export",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    "1-0:62.7.0": {
        "name": "Power L3 Export",
        "unit": UnitOfPower.KILO_WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:solar-power",
    },
    # Phase reactive power import
    "1-0:23.7.0": {
        "name": "Reactive Power L1 Import",
        "unit": UnitOfReactivePower.KILO_VOLT_AMPERE_REACTIVE,
        "device_class": SensorDeviceClass.REACTIVE_POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "1-0:43.7.0": {
        "name": "Reactive Power L2 Import",
        "unit": UnitOfReactivePower.KILO_VOLT_AMPERE_REACTIVE,
        "device_class": SensorDeviceClass.REACTIVE_POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "1-0:63.7.0": {
        "name": "Reactive Power L3 Import",
        "unit": UnitOfReactivePower.KILO_VOLT_AMPERE_REACTIVE,
        "device_class": SensorDeviceClass.REACTIVE_POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    # Phase reactive power export
    "1-0:24.7.0": {
        "name": "Reactive Power L1 Export",
        "unit": UnitOfReactivePower.KILO_VOLT_AMPERE_REACTIVE,
        "device_class": SensorDeviceClass.REACTIVE_POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "1-0:44.7.0": {
        "name": "Reactive Power L2 Export",
        "unit": UnitOfReactivePower.KILO_VOLT_AMPERE_REACTIVE,
        "device_class": SensorDeviceClass.REACTIVE_POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
    "1-0:64.7.0": {
        "name": "Reactive Power L3 Export",
        "unit": UnitOfReactivePower.KILO_VOLT_AMPERE_REACTIVE,
        "device_class": SensorDeviceClass.REACTIVE_POWER,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:sine-wave",
    },
}
