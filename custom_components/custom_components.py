"""
Update your custom_components.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/custom_components
"""
import logging
import os
import subprocess
from datetime import timedelta

import requests
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.dispatcher import async_dispatcher_send

__version__ = '0.0.5'

DOMAIN = 'custom_components'
DATA_CC = 'custom_components_data'
CONF_HIDE_SENSOR = 'hide_sensor'
SIGNAL_SENSOR_UPDATE = 'custom_components_update'

ATTR_COMPONENT = 'component'

INTERVAL = timedelta(days=1)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_HIDE_SENSOR, default=False): cv.boolean,
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

BASE_REPO = 'https://raw.githubusercontent.com/custom-components/'
VISIT_REPO = 'https://github.com/custom-components/%s'
SENSOR_URL = 'https://raw.githubusercontent.com/custom-components/sensor.custom_components/master/custom_components/sensor/custom_components.py'
VERSION_URL = BASE_REPO + 'information/master/repos.json'

def setup(hass, config):
    """Set up the component."""
    _LOGGER.info('version %s is starting, if you have ANY issues with this, please report \
                  them here: https://github.com/custom-components/%s',
                 __version__, __name__.split('.')[1])
    conf_dir = str(hass.config.path())
    controller = CustomComponents(hass, conf_dir)
    hide_sensor = config[DOMAIN][CONF_HIDE_SENSOR]

    def update_all_service(call):
        """Set up service for manual trigger."""
        controller.update_all()

    def update_single_service(call):
        """Set up service for manual trigger."""
        controller.update_single(call.data.get(ATTR_COMPONENT))

    track_time_interval(hass, controller.cache_versions, INTERVAL)
    hass.services.register(
        DOMAIN, 'update_all', update_all_service)
    hass.services.register(
        DOMAIN, 'update_single', update_single_service)
    hass.services.register(
        DOMAIN, 'check_all', controller.cache_versions)
    if not hide_sensor:
        sensor_dir = str(hass.config.path("custom_components/sensor/"))
        sensor_file = 'custom_components.py'
        sensor_full_path = sensor_dir + sensor_file
        if not os.path.isfile(sensor_full_path):
            _LOGGER.debug('Could not find %s in %s, trying to download.', sensor_file, sensor_dir)
            response = requests.get(SENSOR_URL)
            if response.status_code == 200:
                _LOGGER.debug('Checking folder structure')
                directory = os.path.dirname(sensor_dir)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open(sensor_full_path, 'wb+') as sensorfile:
                    sensorfile.write(response.content)
            else:
                _LOGGER.critical('Failed to download sensor from %s', SENSOR_URL)
        load_platform(hass, 'sensor', DOMAIN)
    return True


class CustomComponents:
    """Custom components controller."""
    def __init__(self, hass, conf_dir):
        self.hass = hass
        self.conf_dir = conf_dir
        self.components = None
        self.hass.data[DATA_CC] = {}
        self.cache_versions(None) # Force a cache update on startup

    def cache_versions(self, time):
        """Cache"""
        self.components = self.get_installed_components()
        self.hass.data[DATA_CC] = {} # Empty list to start from scratch
        if self.components:
            for component in self.components:
                localversion = self.get_local_version(component[1])
                remoteversion = self.get_remote_version(component[0])
                if remoteversion:
                    has_update = (remoteversion != False and remoteversion != localversion)
                    self.hass.data[DATA_CC][component[0]] = {
                        "local": localversion,
                        "remote": remoteversion,
                        "has_update": has_update,
                    }
                    self.hass.data[DATA_CC]['domain'] = DOMAIN
                    self.hass.data[DATA_CC]['repo'] = VISIT_REPO
            async_dispatcher_send(self.hass, SIGNAL_SENSOR_UPDATE)

    def update_all(self):
        """Update all components"""
        for component in self.components:
            try:
                if self.hass.data[DATA_CC][component[0]]['has_update']:
                    self.update_single(component[0], component[1])
            except:
                _LOGGER.debug('Skipping upgrade for %s, no update available', component[0])

    def update_single(self, component, componentpath=None):
        """Update one components"""
        if component in self.hass.data[DATA_CC]:
            if not componentpath:
                if '.' not in component:
                    componentpath = self.conf_dir + '/custom_components/' + component + '.py'
                else:
                    domain = component.split('.')[0]
                    platform = component.split('.')[1]
                    componentpath = self.conf_dir + '/custom_components/' + domain + '/' + platform + '.py'
            if self.hass.data[DATA_CC][component]['has_update']:
                self.download_component(component, componentpath)
                _LOGGER.info('Upgrade of %s from version %s to version %s complete', component, self.hass.data[DATA_CC][component]['local'], self.hass.data[DATA_CC][component]['remote'])
                self.hass.data[DATA_CC][component]['local'] = self.hass.data[DATA_CC][component]['remote']
                self.hass.data[DATA_CC][component]['has_update'] = False
                async_dispatcher_send(self.hass, SIGNAL_SENSOR_UPDATE)
            else:
                _LOGGER.debug('Skipping upgrade for %s, no update available', component)
        else:
            _LOGGER.error('Upgrade failed, no valid component specified %s', component)

    def download_component(self, component, componentpath):
        """Downloading new component"""
        _LOGGER.debug('Downloading new version of %s, to %s', component, componentpath)
        if '.' not in component:
            url = BASE_REPO + component + '/master/custom_components/' + component + '.py'
        else:
            domain = component.split('.')[0]
            platform = component.split('.')[1]
            url = BASE_REPO + component + '/master/custom_components/' + domain + '/' + platform + '.py'
        response = requests.get(url)
        if response.status_code == 200:
            with open(componentpath, 'wb') as component_file:
                component_file.write(response.content)

    def get_installed_components(self):
        """Get all components in use from the custom_components dir"""
        _LOGGER.debug('Checking for installed components in  %s/custom_components', self.conf_dir)
        components = []
        componentdir = ['/custom_components']
        for dir in os.listdir(self.conf_dir + '/custom_components'):
            if not dir.endswith(".py") and not dir.endswith("_"):
                if os.path.isdir(self.conf_dir + '/custom_components/' + dir):
                    componentdir.append('/custom_components/' + dir)
        _LOGGER.debug(componentdir)
        for path in componentdir:
            for component in os.listdir(self.conf_dir + path):
                if component.endswith(".py") and not component.endswith("c") and not component.startswith("_"):
                    componentpath = self.conf_dir + path + '/' + component
                    component.split('.')[0]
                    if path == '/custom_components':
                        componentfullname = component.split('.')[0]
                    else:
                        domain = path.split('/')[-1]
                        platform = component.split('.')[0]
                        componentfullname = domain + '.' + platform
                    components.append([componentfullname, componentpath])
        _LOGGER.debug(components)
        return components

    def get_remote_version(self, component):
        """Return the remote version if any."""
        response = requests.get(VERSION_URL)
        if response.status_code == 200:
            try:
                remoteversion = response.json()[component]['version']
                _LOGGER.debug('Remote version of %s is %s', component, remoteversion)
            except:
                remoteversion = False
                _LOGGER.debug('Remote version of %s could not be found...', component)
        else:
            _LOGGER.debug('Could not get the remote version for %s', component)
            remoteversion = False
        if remoteversion == '':
            remoteversion = False
        return remoteversion

    def get_local_version(self, componentpath):
        """Return the local version if any."""
        localversion = None
        with open(componentpath, 'r') as local:
            for line in local.readlines():
                if '__version__' in line:
                    localversion = line.split("'")[1]
                    break
        local.close()
        if not localversion:
            return False
            _LOGGER.debug('Could not get the local version for %s', componentpath)
        else:
            return localversion
            _LOGGER.debug('Local version of %s is %s', componentpath, localversion)
