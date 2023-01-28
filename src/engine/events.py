class Event:
    def __init__(self, **kwargs):
        for i, j in kwargs.items():
            self.__setattr__(i, j)

    @property
    def type(self):
        return self.__class__.__name__

    def property(self, prop):
        try:
            return self.__getattribute__(prop)
        except AttributeError:
            return None


class GenericEvent(Event):
    pass


class ButtonClickedEvent(Event):
    pass


class EventsManager:
    MAX_EVENTS = 100

    def __init__(self):
        self._events: list[Event] = []

        def function(event):
            if isinstance(event, Event):
                pass

        self.process_event = function

    def set_process_event(self, function):
        self.process_event = function

    def process_all_events(self):
        for i in self.get():
            self.process_event(i)
        self.clear()

    def clear(self):
        self._events.clear()

    def post(self, event=None, **kwargs):
        if len(self._events) < self.MAX_EVENTS:
            if event:
                self._events.append(event)
            else:
                self._events.append(GenericEvent(**kwargs))

    def get(self, clear=False):
        if clear:
            events = self._events.copy()
            self._events.clear()
            return events
        else:
            return self._events

    def poll(self):
        return self._events.pop(0)
