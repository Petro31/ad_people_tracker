# Home Assistant People Tracking Sensor

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
<br><a href="https://www.buymeacoffee.com/Petro31" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-black.png" width="150px" height="35px" alt="Buy Me A Coffee" style="height: 35px !important;width: 150px !important;" ></a>

_People Tracking Sesnor app for AppDaemon._

Creates a sensor that tracks the number of people at home.  Also creates gramatically correct lists of formated names at home.

The sensor contains the following information:
* Number of people at home, including guests.
* A list of people at home, sorted by first name.  Guests are always last.  e.g. A, B, and guests
* Removes plural letters from device tracker names.  e.g. `Petro's iPhone` will be reduced to `Petro`.
* A gramatically correct string using the conjunction 'and'  e.g. A, B, and C
* A gramatically correct string using the conjunction 'or'.  e.g. A, B, or C

## Installation

Download the `people_tracker` directory from inside the `apps` directory here to your local `apps` directory, then add the configuration to enable the `hacs` module.

## Example App configuration

#### Basic
```yaml
# Monitors all events in INFO log level
events:
  module: people_tracker
  class: PeopleTracker
  guest_entity_id: input_boolean.guests
  entities:
  - device_tracker.petro
  - person.wife
```

#### Advanced
```yaml
# Creates a sensor for Spanish, using 'y' for 'and' and 'o' for 'or'.
events:
  module: people_tracker
  class: PeopleTracker
  guest_entity_id: input_boolean.invitados
  entities:
  - device_tracker.petro
  - person.wife
  name: Gente en Casa
  guests_name: invitados
  and: y
  or: o
  log_level: INFO
```

#### App Configuration
key | optional | type | default | description
-- | -- | -- | -- | --
`module` | False | string | people_tracker | The module name of the app.
`class` | False | string | PeopleTracker | The name of the Class.
`entities` | False | list | | A list of people or device_tracker entity_ids.
`guest_entity_id` | True | string | | A input_boolean or binary_sensor that determines if guests are home.
`name` | True | string | `People Tracker` | Name of the created sensor.
`guests_name` | True | string | `guests` | Name displayed in tracker when guests are home.
`and` | True | string | `and` | Conjunction used for representing `A, B, and C.
`or` | True | string | `or` | Conjunction used for representing `A, B, or C.
`log_level` | True | `'INFO'` &#124; `'DEBUG'` | `'INFO'` | Lazy log level, it pushes all logs to a specific level so you don't need to restart appdaemon.
