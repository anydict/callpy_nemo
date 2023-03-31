from dataclasses import dataclass
from datetime import datetime


@dataclass
class TriggerEvent:
    app: str
    tag: str
    lead_id: str
    status: str
    msg: str
    asterisk_time: str
    trigger_time: str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f+0000')

    def diff_time(self) -> float:
        a = datetime.strptime(self.trigger_time, "%Y-%m-%dT%H:%M:%S.%f+0000")
        b = datetime.strptime(self.asterisk_time, "%Y-%m-%dT%H:%M:%S.%f+0000")
        c = b - a
        return c.total_seconds()
