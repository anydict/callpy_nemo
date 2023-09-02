from dataclasses import dataclass


@dataclass
class TriggerEvent:
    app: str
    asterisk_id: str
    event_type: str
    external_time: str
    trigger_time: str
    delay: float
    tag: str
    call_id: str
    status: str
    value: str
