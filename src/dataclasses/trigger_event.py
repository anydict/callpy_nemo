from dataclasses import dataclass
from datetime import datetime

UNKNOWN = 'unknown'


@dataclass
class TriggerEvent:
    app: str
    asterisk_id: str
    event_type: str
    asterisk_time: str
    trigger_time: str
    delay: float
    tag: str
    lead_id: str
    status: str
    value: str

    def __init__(self, event: dict):
        self.app: str = event.get('application') or UNKNOWN
        self.asterisk_id: str = event.get('asterisk_id') or UNKNOWN
        self.event_type: str = event.get('type') or UNKNOWN

        self.asterisk_time: str = (event.get('timestamp') or datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))[:23]
        self.trigger_time: str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.delay: float = self.calc_delay()

        self.tag: str = self.get_tag_from_event(event, self.event_type)
        self.lead_id: str = self.get_lead_id_from_event(event, self.event_type)
        self.status: str = self.get_status_from_event(event, self.event_type)
        self.value: str = self.get_value_from_event(event, self.event_type)

    def calc_delay(self) -> float:
        a = datetime.strptime(self.asterisk_time, "%Y-%m-%dT%H:%M:%S.%f")
        b = datetime.strptime(self.trigger_time, "%Y-%m-%dT%H:%M:%S.%f")
        return (b - a).total_seconds()

    @staticmethod
    def get_tag_from_event(event: dict, event_type: str):
        tag = UNKNOWN
        if event_type in ('ChannelDialplan', 'ChannelCreated', 'ChannelVarset'):
            if '-id-' in event.get('channel').get('id'):
                tag = event.get('channel').get('id').split('-id-')[0]

        elif event_type == 'Dial' and '-id-' in event.get('peer').get('id'):
            tag = event.get('peer').get('id').split('-id-')[0]

        elif event_type == 'BridgeCreated' and '-id-' in event.get('bridge').get('id'):
            tag = event.get('bridge').get('id').split('-id-')[0]

        elif event_type == 'ChannelDtmfReceived' and '-id-' in event.get('channel').get('id'):
            tag = event.get('channel').get('id').split('-id-')[0]

        return tag

    @staticmethod
    def get_lead_id_from_event(event: dict, event_type: str):
        lead_id = UNKNOWN
        if event_type in ('ChannelDialplan', 'ChannelCreated', 'ChannelVarset'):
            if '-id-' in event.get('channel').get('id'):
                lead_id = event.get('channel').get('id').split('-id-')[1]

        elif event_type == 'Dial' and '-id-' in event.get('peer').get('id'):
            lead_id = event.get('peer').get('id').split('-id-')[1]

        elif event_type == 'BridgeCreated' and '-id-' in event.get('bridge').get('id'):
            lead_id = event.get('bridge').get('id').split('-id-')[1]

        elif event_type == 'ChannelDtmfReceived' and '-id-' in event.get('channel').get('id'):
            lead_id = event.get('channel').get('id').split('-id-')[1]

        return lead_id

    @staticmethod
    def get_status_from_event(event: dict, event_type: str):
        status = UNKNOWN
        if event_type == 'ChannelCreated':
            status = 'READY'

        elif event_type == 'Dial':
            if event.get("dialstatus", "") == "":
                status = "AppDial1"
            else:
                status = event.get("dialstatus")

        elif event_type == 'ChannelVarset':
            if event.get("variable") == 'STASISSTATUS':
                status = f'VARSET_STASISSTATUS{event.get("value")}'
            else:
                status = f'VARSET_{event.get("variable")}'

        elif event_type == 'ChannelDialplan':
            status = event.get("dialplan_app")

        elif event_type == 'BridgeCreated':
            status = 'READY'

        elif event_type == 'ChannelDtmfReceived':
            status = f'dtmf_{event.get("digit")}'

        return status.upper()

    @staticmethod
    def get_value_from_event(event: dict, event_type: str):
        if event_type == 'ChannelDtmfReceived':
            return event.get("digit")

        elif event_type in 'ChannelVarset':
            return event.get("variable")

        elif event_type in 'Dial':
            return event.get("dialstring")

        else:
            return None
