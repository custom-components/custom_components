# custom_component to update custom_components

A component which allows you to update your custom_components automatically and monitor their versions from the UI. It exposes three services: `custom_components.download_single`, `custom_components.update_all`, `custom_components.update_single` and `custom_components.check_all`.

To get the best use for this component, use together with [tracker-card](https://github.com/ciotlosm/custom-lovelace/tree/master/tracker-card)\
**To use this card you can _NOT_ set `hide_sensor` to `true`**

⚠️ For now this wil ONLY work if your components if from https://github.com/custom-components

## Installation

To get started put `/custom_components/custom_components.py`  
here: `<config directory>/custom_components/custom_components.py` 

## Configuration
  
| key | default | required | description
| --- | --- | --- | ---
| **hide_sensor** | False | no | Download and register the sensor used by the [tracker-card](https://github.com/ciotlosm/custom-lovelace/tree/master/tracker-card), can be `True`/`False`

☢️ It is strongly adviced to not have this auto update

## Example

In your `configuration.yaml`:

```yaml
custom_components:
```

ℹ️ The sensor will get discovered automatically if installation was done correctly.

## Debug logging

In your `configuration.yaml`

```yaml
logger:
  default: warn
  logs:
    custom_components.custom_components: debug
    custom_components.sensor.custom_components: debug
```

## Update single component

You can update a single component by passing which component you want to update to the  `custom_components.update_single` service.

### From dev-service

Service: `custom_components.update_single`

Service Data:

```json
{
  "component":"sensor.authenticated"
}
```

Service: `custom_components.download_single`

Service Data:

```json
{
  "component":"sensor.authenticated"
}
```
