from dataclasses import dataclass


class Trigger(object):
    def __init__(self, trigger_raw: dict):
        """
        Create new trigger object

        @param trigger_raw - a dictionary containing trigger information
        @return None
        """
        self.trigger_tag: str = trigger_raw.get('trigger_tag', 'unknown')
        self.trigger_status: str = trigger_raw.get('trigger_status', 'unknown')
        self.action: str = trigger_raw.get('action', 'unknown')
        self.active: bool = trigger_raw.get('active', True)
        self.func: bool = trigger_raw.get('func', None)


@dataclass
class Dialplan(object):
    def __init__(self, raw_dialplan: dict, app: str):
        """
        This is a class constructor that initializes a Dialplan object with the given parameters.

        @param raw_dialplan: dict - A dictionary containing the raw dialplan data.
        @param app: str - The application to use.
        @return Dialplan object with the given parameters.
        """
        self.raw_dialplan = raw_dialplan
        self.app: str = app

        self.name: str = raw_dialplan.get('name', 'unknown')
        self.tag: str = raw_dialplan.get('tag', 'unknown')
        self.type: str = raw_dialplan.get('type', 'unknown')
        self.status: str = raw_dialplan.get('status', 'init')
        self.params: dict = raw_dialplan.get('params', {})

        list_trigger = []
        if raw_dialplan.get('triggers', None):
            for trigger_raw in raw_dialplan.get('triggers'):
                list_trigger.append(Trigger(trigger_raw))
        self.triggers: list[Trigger] = list_trigger

        list_dialplan = []
        if raw_dialplan.get('content', None):
            for dialplan in raw_dialplan.get('content'):
                list_dialplan.append(Dialplan(dialplan, app))
        self.content: list[Dialplan] = list_dialplan
