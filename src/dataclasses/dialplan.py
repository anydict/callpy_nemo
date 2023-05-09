from dataclasses import dataclass


class Trigger(object):
    def __init__(self, trigger_raw: dict):
        self.trigger_tag: str = trigger_raw.get('trigger_tag', 'unknown')
        self.trigger_status: str = trigger_raw.get('trigger_status', 'unknown')
        self.action: str = trigger_raw.get('action', 'unknown')
        self.active: bool = trigger_raw.get('active', True)


@dataclass
class Dialplan(object):
    def __init__(self, dialplan_raw: dict, app: str):
        self.app: str = app
        self.name: str = dialplan_raw.get('name', 'unknown')
        self.tag: str = dialplan_raw.get('tag', 'unknown')
        self.type: str = dialplan_raw.get('type', 'unknown')
        self.status: str = dialplan_raw.get('status', 'init')
        self.params: dict = dialplan_raw.get('params', {})

        list_trigger = []
        if dialplan_raw.get('triggers', None):
            for trigger_raw in dialplan_raw.get('triggers'):
                list_trigger.append(Trigger(trigger_raw))
        self.triggers: list[Trigger] = list_trigger

        list_dialplan = []
        if dialplan_raw.get('content', None):
            for dialplan in dialplan_raw.get('content'):
                list_dialplan.append(Dialplan(dialplan, app))
        self.content: list[Dialplan] = list_dialplan
