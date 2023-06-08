from dataclasses import dataclass
from datetime import datetime
from typing import Union

UNKNOWN = 'UNKNOWN'


@dataclass
class TriggerEvent:
    app: str
    asterisk_id: str
    event_type: str
    external_time: str
    trigger_time: str
    delay: float
    tag: str
    druid: str
    status: str
    value: str

    def __init__(self, event: dict):
        self.app: str = event.get('application') or UNKNOWN
        self.asterisk_id: str = event.get('asterisk_id') or UNKNOWN
        self.event_type: str = event.get('type') or UNKNOWN
        self.trigger_time: str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        self.external_time: str = self.fix_iso_timestamp(event.get('timestamp'))

        self.delay: float = self.calc_delay()

        self.tag: str = self.get_tag_from_event(event, self.event_type)
        self.druid: str = self.get_druid_from_event(event, self.event_type)
        self.status: str = self.get_status_from_event(event, self.event_type)
        self.value: str = self.get_value_from_event(event, self.event_type)

    def calc_delay(self) -> float:
        a = datetime.strptime(self.external_time, "%Y-%m-%dT%H:%M:%S.%f")
        b = datetime.strptime(self.trigger_time, "%Y-%m-%dT%H:%M:%S.%f")
        return (b - a).total_seconds()

    @staticmethod
    def fix_iso_timestamp(var_time: Union[str, None]):
        """ Converting the date to the correct string format """

        if var_time == '':
            return var_time
        elif len(str(var_time)) > 23:
            # 2023-05-16T00:33:52.951+0300 to 2023-05-16T00:33:52.951000
            return f'{var_time[:23]}000'
        else:
            # other cases return current date (example: 2023-05-16T00:31:03.264071)
            return datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')

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
            if '-id-' in event.get('channel').get('id'):
                tag = event.get('channel').get('id').split('-id-')[0]

        elif event_type == 'Dial' and '-id-' in event.get('peer').get('id'):
            tag = event.get('peer').get('id').split('-id-')[0]

        elif event_type in ('BridgeCreated', 'ChannelEnteredBridge', 'ChannelLeftBridge', 'BridgeDestroyed'):
            if '-id-' in event.get('bridge').get('id'):
                tag = event.get('bridge').get('id').split('-id-')[0]

        elif event_type in ('PlaybackStarted', 'PlaybackFinished'):
            if '-id-' in event.get('playback').get('id'):
                tag = event.get('playback').get('id').split('-id-')[0]

        return tag

    @staticmethod
    def get_druid_from_event(event: dict, event_type: str):
        druid = UNKNOWN
        if event_type == 'ExternalEvent':
            druid = event.get('druid')
        elif event_type in ('ChannelDialplan',
                            'ChannelCreated',
                            'ChannelVarset',
                            'ChannelDtmfReceived',
                            'ChannelStateChange',
                            'ChannelDestroyed',
                            'ChannelHangupRequest',
                            'StasisStart',
                            'StasisEnd'):
            if '-id-' in event.get('channel').get('id'):
                druid = event.get('channel').get('id').split('-id-')[1]

        elif event_type == 'Dial' and '-id-' in event.get('peer').get('id'):
            druid = event.get('peer').get('id').split('-id-')[1]

        elif event_type in ('BridgeCreated', 'ChannelEnteredBridge', 'ChannelLeftBridge', 'BridgeDestroyed'):
            if '-id-' in event.get('bridge').get('id'):
                druid = event.get('bridge').get('id').split('-id-')[1]

        elif event_type in ('PlaybackStarted', 'PlaybackFinished'):
            if '-id-' in event.get('playback').get('id'):
                druid = event.get('playback').get('id').split('-id-')[1]

        return druid

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

        elif event_type in 'ChannelVarset':
            return event.get("value")

        elif event_type in 'Dial':
            return event.get('dialstring')

        elif event_type in ('PlaybackStarted'):
            return event.get('playback').get('media_uri') or ''

        elif event_type in ('PlaybackFinished'):
            return event.get('playback').get('state') or ''

        else:
            return ""
