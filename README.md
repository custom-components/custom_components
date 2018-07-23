# custom_component to update custom_components
***
***
**No more updates are added to this component, use this instead:**\
https://github.com/custom-components/custom_updater
***
***

A component which allows you to update your custom_components automatically and monitor their versions from the UI. It exposes three services: `custom_components.download_single`, `custom_components.update_all`, `custom_components.update_single` and `custom_components.check_all`.

To get the best use for this component, use together with [tracker-card](https://github.com/ciotlosm/custom-lovelace/tree/master/tracker-card)\

⚠️ For now this wil ONLY work if your components if from https://github.com/custom-components

## Installation

To get started put `/custom_components/custom_components.py`  
here: `<config directory>/custom_components/custom_components.py` 

## Example

In your `configuration.yaml`:

```yaml
custom_components:
```

## Debug logging

In your `configuration.yaml`

```yaml
logger:
  default: warn
  logs:
    custom_components.custom_components: debug
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
