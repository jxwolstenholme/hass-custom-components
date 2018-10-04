"""
Support for BT Smart Hub device tracking in Home Assistant.

"""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.device_tracker import (DOMAIN, PLATFORM_SCHEMA,
                                                     DeviceScanner)
from homeassistant.const import CONF_HOST

REQUIREMENTS = ['btsmarthub_devicelist==0.1.1']

_LOGGER = logging.getLogger(__name__)

CONF_DEFAULT_IP = '192.168.1.254'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST, default=CONF_DEFAULT_IP): cv.string,
})


def get_scanner(hass, config):
    """Return a BT SmartHub scanner if successful."""
    scanner = BTSmartHubScanner(config[DOMAIN])

    return scanner if scanner.success_init else None


class BTSmartHubScanner(DeviceScanner):
    """This class queries a BT Smart Hub."""

    def __init__(self, config):
        """Initialise the scanner."""

        _LOGGER.info("Initialising BT Smart Hub")
        self.host = config[CONF_HOST]
        self.last_results = {}

        # Test the router is accessible
        data = self.get_bt_smarthub_data()
        self.success_init = data is not None

    def scan_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        self._update_info()

        return [client['mac'] for client in self.last_results]

    def get_device_name(self, device):

        if not self.last_results:
            return None
        for client in self.last_results:
            if client['mac'] == device:
                return client['host']
        return None


    def _update_info(self):
        """Ensure the information from the BT Home Hub 5 is up to date.

         Return boolean if scanning successful
        """

        if not self.success_init:
           return False

        _LOGGER.info("Scanning")
        data = self.get_bt_smarthub_data()
        if not data:
            _LOGGER.warning("Error scanning devices")
            return False

        clients = [client for client in data.values()]
        self.last_results = clients
        return True

    def get_bt_smarthub_data(self):
        """Retrieve data from BT Smarthub and return parsed result"""
        import btsmarthub_devicelist

        data = btsmarthub_devicelist.get_devicelist(router_ip=self.host, only_active_devices=True)
        devices = {}
        for device in data:
            try:
                devices[device['UserHostName']] = {
                    'ip': device['IPAddress'],
                    'mac': device['PhysAddress'],
                    'host': device['UserHostName'],
                    'status': device['Active']
                }
            except (KeyError, 'no'):
                pass
        return devices
