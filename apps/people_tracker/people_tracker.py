import appdaemon.plugins.hass.hassapi as hass
import voluptuous as vol

CONF_MODULE = 'module'
CONF_CLASS = 'class'
CONF_ENTITIES = 'entities'
CONF_GUESTS_ENTITY = 'guest_entity_id'
CONF_AND = 'and'
CONF_OR = 'or'
CONF_LOG_LEVEL = 'log_level'
CONF_NAME = 'name'
CONF_GUESTS_NAME = 'guests_name'

CONF_GUESTS = 'guests'

SENSOR_NAME = "People Tracker"

LOG_ERROR = 'ERROR'
LOG_DEBUG = 'DEBUG'
LOG_INFO = 'INFO'

ATTRIBUTE_ICON = 'icon'
ATTRIBUTE_FRIENDLY_NAME = 'friendly_name'
ATTRIBUTE_PEOPLE = 'people'
ATTRIBUTE_COUNT = 'count'

STATE_HOME = 'home'
STATE_ON = 'on'

STATES_HOME = [STATE_HOME, STATE_ON]

APP_SCHEMA = vol.Schema({
    vol.Required(CONF_MODULE): str,
    vol.Required(CONF_CLASS): str,
    vol.Required(CONF_ENTITIES): [ str ],
    vol.Optional(CONF_NAME): str,
    vol.Optional(CONF_GUESTS_NAME, default=CONF_GUESTS): str,
    vol.Optional(CONF_GUESTS_ENTITY): str,
    vol.Optional(CONF_AND, default=CONF_AND): str,
    vol.Optional(CONF_OR, default=CONF_OR): str,
    vol.Optional(CONF_LOG_LEVEL, default=LOG_DEBUG): vol.Any(LOG_INFO, LOG_DEBUG),
    })

class PeopleTracker(hass.Hass):
    def initialize(self):
        args = APP_SCHEMA(self.args)

        # Set Lazy Logging (to not have to restart appdaemon)
        self._level = args.get(CONF_LOG_LEVEL)

        self.entities = args.get(CONF_ENTITIES, [])
        self.guest_entity_id = args.get(CONF_GUESTS_ENTITY)
        self._guest_name = args.get(CONF_GUESTS_NAME)

        name = args.get(CONF_NAME, SENSOR_NAME)
        object_id = name.replace(' ','_').lower()

        self._and = args.get(CONF_AND)
        self._or = args.get(CONF_OR)

        self._sensor = f"sensor.{object_id}"

        self.log(self.get_state(self.guest_entity_id, attribute='all'), level = self._level)

        self._people = []

        self.handles = []

        for entity_id in self.entities:
            handle = self.listen_state(self.track_person, entity = entity_id)
            self.handles.append(handle)

        if self.guest_entity_id:
            handle = self.listen_state(self.track_guests, entity = self.guest_entity_id)
            self.handles.append(handle)

        #Populate people on startup.
        self.find_people()

        self.log(self.people_conjunction(), level = self._level)

        # initialize sensor
        attrs = {ATTRIBUTE_FRIENDLY_NAME:name}
        self._set_people_state(**attrs)

    def clean_persons_name(self, entity_id):
        """ 
        clean the name, de-plualize it in case this is a phone and we 
          don't have a person.
        """
        name = self.friendly_name(entity_id)
        name = name.split(' ')[0]
        if name.endswith("'s"):
            name = name[:-2]
        return name.title()

    def track_person(self, entity, attribute, old, new, kwargs):
        name = self.clean_persons_name(entity)
        if new in STATES_HOME:
            self.add_person(name)
        else:
            self.remove_person(name)

    def add_person(self, name):
        # I forget why this was added but it was added for a reason.
        # Most likely because I have more than 1 device tracker per person
        # and this was created before Person existed.  Leave it for now.
        if name not in self._people and name[:-1] not in self._people:
            before = str(self._people)
            self._people.append(name)
            self._people.sort()
            after = str(self._people)
            self.log('%s -> %s'%(before, after), level = self._level)
            self._set_people_state()

    def remove_person(self, name):
        if name in self._people:
            before = str(self._people)
            idx = self._people.index(name)
            self._people.pop(idx)
            after = str(self._people)
            self.log('%s -> %s'%(before, after), level = self._level)
            self._set_people_state()

    def track_guests(self, entity, attribute, old, new, kwargs):
        if new in ['on','enabled','home']:
            self.add_person(self._guest_name)
        else:
            self.remove_person(self._guest_name)

    def find_people(self):
        for entity_id in self.entities:
            if self.get_state(entity_id) in [ 'home' ]:
                name = self.clean_persons_name(entity_id)
                self.add_person(name)
        if self.guest_entity_id:
            if self.get_state(self.guest_entity_id) in ['on','enabled','home']:
                self.add_person(self._guest_name)

    @property
    def people_at_home(self): return self._people

    def people_conjunction(self, conjunction='and'):
        people = self.people_at_home
        if len(people) == 0:
            return "Unknown"
        elif len(people) == 1:
            return people[0]
        elif len(people) == 2:
            return ' {} '.format(conjunction).join(people)
        else:
            return "{}, {} {}".format(', '.join(people[:-1]), conjunction, people[-1])

    def people_used_sensor(self, sensor_name):
        """ Use this when you want to call out someone using a device, this is not exposed to the sesnor. """
        if not self.people_at_home:
            return "Unknown person used the {}.".format(sensor_name)
        else:
            people = self.people_conjunction('or')
            return '{} used the {}.'.format(people, sensor_name)
        
    @property
    def _icon(self):
        icons = [ 'account-off', 'account', 'account-multiple' ]
        count = len(self._people)
        if count < 0:
            return 'mdi:account-alert'
        elif 0 <= count <= 2:
            return f'mdi:{icons[count]}'
        else:
            return 'mdi:account-group'
            
    def _set_people_state(self, **kwargs):
        state = str(len(self._people))

        attributes = {}
        attributes[CONF_AND] = self.people_conjunction(self._and)
        attributes[CONF_OR] = self.people_conjunction(self._or)
        attributes[ATTRIBUTE_PEOPLE] = self.people_at_home
        attributes[ATTRIBUTE_ICON] = self._icon
        attributes[ATTRIBUTE_COUNT] = len(self._people)
        for k, v in kwargs.items():
            attributes[k] = v
        
        self.log(f"{self._sensor}: {state}, attributes={attributes}", level = self._level)
        
        self.set_state(self._sensor, state=state, attributes=attributes)
    
    def terminate(self):
        for handle in self.handles:
            self.cancel_listen_state(handle)
