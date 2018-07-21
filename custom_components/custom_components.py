"""
Update your custom_components.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/custom_components
"""
import logging
import os
from datetime import timedelta
import time

import requests
from homeassistant.helpers.event import track_time_interval


__version__ = '1.0.0'

DOMAIN = 'custom_components'
DATA_CC = 'custom_components_data'

ATTR_COMPONENT = 'component'

INTERVAL = timedelta(days=1)

_LOGGER = logging.getLogger(__name__)

BASE_REPO = 'https://raw.githubusercontent.com/custom-components/'
VISIT_REPO = 'https://github.com/custom-components/%s'
VERSION_URL = BASE_REPO + 'information/master/repos.json'

def setup(hass, config):
    """Set up the component."""
    _LOGGER.info('version %s is starting, if you have ANY issues with this, please report \
                  them here: https://github.com/custom-components/%s',
                 __version__, __name__.split('.')[1])
    conf_dir = str(hass.config.path())
    controller = CustomComponents(hass, conf_dir)

    def update_all_service(call):
        """Set up service for manual trigger."""
        controller.update_all()

    def update_single_service(call):
        """Set up service for manual trigger."""
        controller.update_single(call.data.get(ATTR_COMPONENT))

    def download_single_service(call):
        """Set up service for manual trigger."""
        controller.download_single(call.data.get(ATTR_COMPONENT))

    track_time_interval(hass, controller.cache_versions, INTERVAL)
    hass.services.register(
        DOMAIN, 'update_all', update_all_service)
    hass.services.register(
        DOMAIN, 'update_single', update_single_service)
    hass.services.register(
        DOMAIN, 'download_single', download_single_service)
    hass.services.register(
        DOMAIN, 'check_all', controller.cache_versions)
    return True


class CustomComponents:
    """Custom components controller."""
    def __init__(self, hass, conf_dir):
        self.hass = hass
        self.conf_dir = conf_dir
        self.components = None
        self.hass.data[DATA_CC] = {}
        self.cache_versions() # Force a cache update on startup

    def cache_versions(self):
        """Cache"""
        self.components = self.get_components()
        self.hass.data[DATA_CC] = {} # Empty list to start from scratch
        if self.components:
            for component in self.components:
                localversion = self.get_local_version(component[1])
                remoteversion = self.get_remote_version(component[0])
                if localversion:
                    has_update = (remoteversion != False and remoteversion != localversion)
                    not_local = (remoteversion != False and not localversion)
                    self.hass.data[DATA_CC][component[0]] = {
                        "local": localversion,
                        "remote": remoteversion,
                        "has_update": has_update,
                        "not_local": not_local,
                    }
                    self.hass.data[DATA_CC]['domain'] = DOMAIN
                    self.hass.data[DATA_CC]['repo'] = VISIT_REPO
            self.hass.states.set('sensor.custom_component_tracker', time.time(), self.hass.data[DATA_CC])

    def update_all(self):
        """Update all components"""
        for component in self.components:
            try:
                if self.hass.data[DATA_CC][component[0]]['has_update'] and not self.hass.data[DATA_CC][component[0]]['not_local']:
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
                self.hass.data[DATA_CC][component]['not_local'] = False
                self.hass.states.set('sensor.custom_component_tracker', time.time(), self.hass.data[DATA_CC])
            else:
                _LOGGER.debug('Skipping upgrade for %s, no update available', component)
        else:
            _LOGGER.error('Upgrade failed, no valid component specified %s', component)

    def download_single(self, component):
        """Helper for download_single service"""
        if '.' not in component:
            componentpath = self.conf_dir + '/custom_components/' + component + '.py'
        else:
            domain = component.split('.')[0]
            platform = component.split('.')[1]
            componentpath = self.conf_dir + '/custom_components/' + domain + '/' + platform + '.py'
        self.download_component(component, componentpath)
        _LOGGER.info('Upgrade of %s from version %s to version %s complete', component, self.hass.data[DATA_CC][component]['local'], self.hass.data[DATA_CC][component]['remote'])
        self.hass.data[DATA_CC][component]['local'] = self.hass.data[DATA_CC][component]['remote']
        self.hass.data[DATA_CC][component]['has_update'] = False
        self.hass.data[DATA_CC][component]['not_local'] = False
        self.hass.states.set('sensor.custom_component_tracker', time.time(), self.hass.data[DATA_CC])

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

    def get_components(self):
        """Get all available components"""
        components = []
        response = requests.get(VERSION_URL)
        if response.status_code == 200:
            for component in response.json():
                if '.' not in component:
                    componentpath = self.conf_dir + '/custom_components/' + component + '.py'
                else:
                    domain = component.split('.')[0]
                    platform = component.split('.')[1]
                    componentpath = self.conf_dir + '/custom_components/' + domain + '/' + platform + '.py'

                components.append([component, componentpath])
        else:
            _LOGGER.debug('Could not reach the remote repo')
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
        if os.path.isfile(componentpath):
            with open(componentpath, 'r') as local:
                for line in local.readlines():
                    if '__version__' in line:
                        localversion = line.split("'")[1]
                        break
            local.close()
            if not localversion:
                localv = False
                _LOGGER.debug('Could not get the local version for %s', componentpath)
            else:
                localv = localversion
                _LOGGER.debug('Local version of %s is %s', componentpath, localversion)
        else:
            localv = False
            _LOGGER.debug('File "%s" not found, assuming not installed', componentpath)
        return localv
