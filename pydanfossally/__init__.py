import logging

from pydanfossally.const import THERMOSTAT_DEVICE_TYPE, THERMOSTAT_MODE_AUTO

from .danfossallyapi import *

_LOGGER = logging.getLogger(__name__)

__version__ = "0.0.26"


class DanfossAlly:
    """Danfoss Ally API connector."""

    def __init__(self):
        """Init the API connector variables."""
        self._authorized = False
        self._token = None
        self.devices = {}

        self._api = DanfossAllyAPI()

    def initialize(self, key, secret):
        """Authorize and initialize the connection."""

        token = self._api.getToken(key, secret)

        if token is False:
            self._authorized = False
            _LOGGER.error("Error in authorization")
            return False

        _LOGGER.debug("Token received: %s", self._api.token)
        self._token = self._api.token
        self._authorized = True
        return self._authorized

    def getDeviceList(self):
        """Get device list."""
        devices = self._api.get_devices()

        if devices is None:
            _LOGGER.error("No devices loaded, API error?!")
            return

        if not devices:
            _LOGGER.error("No devices loaded, API connection error?!")
            return

        if not "result" in devices:
            _LOGGER.error("Something went wrong loading devices!")
            return

        for device in devices["result"]:
            self.devices[device["id"]] = {}
            self.devices[device["id"]]["isThermostat"] = device["device_type"] == THERMOSTAT_DEVICE_TYPE
            self.devices[device["id"]]["name"] = device["name"].strip()
            self.devices[device["id"]]["online"] = device["online"]
            self.devices[device["id"]]["update"] = device["update_time"]
            if "model" in device:
                self.devices[device["id"]]["model"] = device["model"]

            temperatures = {}
            for status in device["status"]:
                if status["code"] == "mode":
                    self.devices[device["id"]]["mode"] = status["value"]
                elif status["code"] == "temp_set":
                    temperatures["at_home"] = float(status["value"]) / 10
                elif status["code"] == "leave_home_fast_heat":
                    temperatures["leaving_home"] = float(status["value"]) / 10
                elif status["code"] == "manual_mode_fast":
                    temperatures["manual"] = float(status["value"]) / 10
                elif status["code"] == "temp_current":
                    temperature = float(status["value"])
                    temperature = temperature / 10
                    self.devices[device["id"]]["temperature"] = temperature
                elif status["code"] == "upper_temp":
                    temperature = float(status["value"])
                    temperature = temperature / 10
                    self.devices[device["id"]]["upper_temp"] = temperature
                elif status["code"] == "lower_temp":
                    temperature = float(status["value"])
                    temperature = temperature / 10
                    self.devices[device["id"]]["lower_temp"] = temperature
                elif status["code"] == "va_temperature":
                    temperature = float(status["value"])
                    temperature = temperature / 10
                    self.devices[device["id"]]["temperature"] = temperature
                elif status["code"] == "va_humidity":
                    humidity = float(status["value"])
                    humidity = humidity / 10
                    self.devices[device["id"]]["humidity"] = humidity
                elif status["code"] == "battery_percentage":
                    battery = status["value"]
                    self.devices[device["id"]]["battery"] = battery
                elif status["code"] == "window_state":
                    window = status["value"]
                    if window == "open":
                        self.devices[device["id"]]["window_open"] = True
                    else:
                        self.devices[device["id"]]["window_open"] = False
                elif status["code"] == "child_lock":
                    childlock = status["value"]
                    self.devices[device["id"]]["child_lock"] = childlock
                elif status["code"] == "work_state":
                    self.devices[device["id"]]["work_state"] = status["value"]

            if self.devices[device["id"]]["isThermostat"]:
                setpoint = temperatures[self.devices[device["id"]]["mode"]]
                self.devices[device["id"]]["setpoint"] = setpoint

    @property
    def authorized(self):
        """Return authorized status."""
        return self._authorized

    def setTemperature(self, device_id: str, temp: float) -> bool:
        """Updates temperature setpoint for given device."""
        mode = self.devices[device_id]["mode"];
        temperature = int(temp * 10)

        result = self._api.set_temperature(device_id, mode, temperature)

        return result

    def setMode(self, device_id: str, mode: str) -> bool:
        """Updates operating mode for given device."""
        result = self._api.set_mode(device_id, mode)

        return result
