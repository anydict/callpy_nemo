from datetime import datetime

from loguru import logger

from src.my_dataclasses.trigger_event import TriggerEvent
from src.good_func.good_func import fix_iso_timestamp

UNKNOWN = 'UNKNOWN'


class TriggerEventManager(object):
    def __init__(self):
        self.queue_trigger_events: [TriggerEvent] = []
        self.log = logger.bind(object_id='TriggerEventManager')

    def asterisk_event_to_trigger_event(self, event: dict) -> TriggerEvent:
        app: str = event.get('application') or UNKNOWN
        asterisk_id: str = event.get('asterisk_id') or UNKNOWN
        event_type: str = event.get('type') or UNKNOWN
        trigger_time: str = datetime.now().isoformat()
        external_time: str = fix_iso_timestamp(event.get('timestamp'))

        delay: float = self.calc_delay(external_time, trigger_time)

        # All information about variable asterisk events
        # https://wiki.asterisk.org/wiki/display/AST/Asterisk+20+REST+Data+Models#Asterisk20RESTDataModels-Dial
        tag: str = self.get_tag_from_event(event, event_type)
        call_id: str = self.get_call_id_from_event(event, event_type)
        status: str = self.get_status_from_event(event, event_type)
        value: str = self.get_value_from_event(event, event_type)

        trigger_event = TriggerEvent(app=app,
                                     asterisk_id=asterisk_id,
                                     event_type=event_type,
                                     external_time=external_time,
                                     trigger_time=trigger_time,
                                     delay=delay,
                                     tag=tag,
                                     call_id=call_id,
                                     status=status,
                                     value=value)

        return trigger_event

    def append_queue_trigger_events(self, trigger_event: TriggerEvent):
        self.queue_trigger_events.append(trigger_event)

    def pop_first_queue_trigger_events(self) -> TriggerEvent:
        return self.queue_trigger_events.pop(0)

    @staticmethod
    def calc_delay(a_time, b_time) -> float:
        a = datetime.strptime(a_time, "%Y-%m-%dT%H:%M:%S.%f")
        b = datetime.strptime(b_time, "%Y-%m-%dT%H:%M:%S.%f")
        return (b - a).total_seconds()

    @staticmethod
    def get_tag_from_event(event: dict, event_type: str):
        tag = UNKNOWN
        if event_type == 'ExternalEvent':
            tag = event.get('tag')
        elif event_type in ('ChannelDialplan',
                            'ChannelCreated',
                            'ChannelVarset',
                            'ChannelDtmfReceived',
                            'ChannelStateChange',
                            'ChannelDestroyed',
                            'ChannelHangupRequest',
                            'StasisStart',
                            'StasisEnd'):
            if '-call_id-' in event.get('channel').get('id'):
                tag = event.get('channel').get('id').split('-call_id-')[0]

        elif event_type == 'Dial' and '-call_id-' in event.get('peer').get('id'):
            tag = event.get('peer').get('id').split('-call_id-')[0]

        elif event_type in ('BridgeCreated', 'ChannelEnteredBridge', 'ChannelLeftBridge', 'BridgeDestroyed'):
            if '-call_id-' in event.get('bridge').get('id'):
                tag = event.get('bridge').get('id').split('-call_id-')[0]

        elif event_type in ('PlaybackStarted', 'PlaybackFinished'):
            if '-call_id-' in event.get('playback').get('id'):
                tag = event.get('playback').get('id').split('-call_id-')[0]

        return tag

    @staticmethod
    def get_call_id_from_event(event: dict, event_type: str):
        call_id = UNKNOWN
        if event_type == 'ExternalEvent':
            call_id = event.get('call_id')
        elif event_type in ('ChannelDialplan',
                            'ChannelCreated',
                            'ChannelVarset',
                            'ChannelDtmfReceived',
                            'ChannelStateChange',
                            'ChannelDestroyed',
                            'ChannelHangupRequest',
                            'StasisStart',
                            'StasisEnd'):
            if '-call_id-' in event.get('channel').get('id'):
                call_id = event.get('channel').get('id').split('-call_id-')[1]

        elif event_type == 'Dial':
            if '-call_id-' in event.get('peer').get('id'):
                call_id = event.get('peer').get('id').split('-call_id-')[1]

        elif event_type in ('BridgeCreated', 'ChannelEnteredBridge', 'ChannelLeftBridge', 'BridgeDestroyed'):
            if '-call_id-' in event.get('bridge').get('id'):
                call_id = event.get('bridge').get('id').split('-call_id-')[1]

        elif event_type in ('PlaybackStarted', 'PlaybackFinished'):
            if '-call_id-' in event.get('playback').get('id'):
                call_id = event.get('playback').get('id').split('-call_id-')[1]

        return call_id

    @staticmethod
    def get_status_from_event(event: dict, event_type: str):
        if event_type == 'ExternalEvent':
            status = event.get('status')

        elif event_type == 'ChannelStateChange':
            status = f'{event_type}#{event.get("channel").get("state")}'

        elif event_type == 'Dial':
            status = event_type
            if len(event.get("dialstatus")) > 0:
                status = f'{event_type}#{event.get("dialstatus")}'

        elif event_type == 'ChannelEnteredBridge':
            status = f'{event_type}#{event.get("channel").get("id")}'

        elif event_type == 'ChannelLeftBridge':
            status = f'{event_type}#{event.get("channel").get("id")}'

        elif event_type == 'ChannelVarset':
            status = f'{event_type}#{event.get("variable")}'

        elif event_type == 'ChannelDtmfReceived':
            status = f'{event_type}#{event.get("digit")}'

        elif event_type in ('PlaybackStarted', 'PlaybackFinished'):
            status = event_type

        else:
            status = event_type

        return status

    @staticmethod
    def get_value_from_event(event: dict, event_type: str):
        if event_type == 'ExternalEvent':
            return event.get('value')

        elif event_type == 'ChannelDtmfReceived':
            return event.get("digit")

        elif event_type in 'ChannelStateChange':
            return event.get('channel').get('name')

        elif event_type == 'ChannelHangupRequest':
            return f'{event.get("cause")}'

        elif event_type == 'ChannelDestroyed':
            return f'{event.get("cause_txt")}#{event.get("cause")}'

        elif event_type in 'ChannelVarset':
            return event.get("value")

        elif event_type in 'Dial':
            return event.get('dialstring')

        elif event_type == 'PlaybackStarted':
            return event.get('playback').get('media_uri') or ''

        elif event_type == 'PlaybackFinished':
            return event.get('playback').get('state') or ''

        else:
            return ""
