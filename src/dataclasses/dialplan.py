from dataclasses import dataclass


class Trigger(object):
    def __init__(self, params: dict):
        self.trigger_tag: str = params.get('trigger_tag', 'unknown')
        self.trigger_status: str = params.get('trigger_status', 'unknown')
        self.action: str = params.get('action', 'unknown')


@dataclass
class Dialplan(object):
    def __init__(self, params: dict, app: str):
        self.app: str = app
        self.name: str = params.get('name', 'unknown')
        self.tag: str = params.get('tag', 'unknown')
        self.type: str = params.get('type', 'unknown')
        self.status: str = params.get('status', 'INIT')

        list_trigger = []
        if params.get('triggers', None):
            for trigger in params.get('triggers'):
                list_trigger.append(Trigger(trigger))
        self.triggers: list[Trigger] = list_trigger

        list_dialplan = []
        if params.get('content', None):
            for dialplan in params.get('content'):
                list_dialplan.append(Dialplan(dialplan, app))
        self.content: list[Dialplan] = list_dialplan
