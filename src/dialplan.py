class Dialplan(object):
    def __init__(self, params: dict):
        self.name: str = params.get('name', 'unknown')
        self.tag: str = params.get('tag', 'unknown')
        self.type: str = params.get('type', 'unknown')
        self.status: str = params.get('status', 'init')
        self.trigger_tag: str = params.get('trigger_tag', '')
        self.trigger_status: str = params.get('trigger_status', '')
        list_dialplan = []
        if params.get('content', None):
            for dialplan in params.get('content'):
                list_dialplan.append(Dialplan(dialplan))
        self.content: list[Dialplan] = list_dialplan
