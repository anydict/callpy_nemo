import asyncio
import random
from datetime import datetime
from typing import Union

from loguru import logger

from src.bridge import Bridge
from src.call import Call
from src.config import Config
from src.custom_dataclasses.dialplan import Dialplan
from src.custom_dataclasses.trigger_event import TriggerEvent
from src.http_clients.http_asterisk_client import HttpAsteriskClient


class Room(object):
    """He runs bridges and stores all status inside the room and check room/bridges triggers"""

    def __init__(self, asterisk_client: HttpAsteriskClient, config: Config, call: Call, raw_dialplan: dict, app: str):
        """
        This class is used to manage a conference room.

        @param asterisk_client - HttpAsteriskClient object
        @param config - A Config object
        @param call - A Call object
        @param raw_dialplan - A dictionary representing the dialplan
        @param app - A string representing the app
        @return None
        """
        self.bridges: dict[str, Bridge] = {}
        self.tags_statuses: dict[str, dict] = {}

        self.asterisk_client: HttpAsteriskClient = asterisk_client
        self.config: Config = config
        self.call_id: str = call.call_id
        self.call: Call = call
        self.room_plan: Dialplan = Dialplan(raw_dialplan=raw_dialplan, app=app)  # Each room has its own Dialplan
        self.tag: str = self.room_plan.tag

        self.bridges_plan: list[Dialplan] = self.room_plan.content
        self.room_id: str = f'{self.tag}-call_id-{call.call_id}'

        self.log = logger.bind(object_id=self.room_id)
        asyncio.create_task(self.add_tag_status(tag=self.tag,
                                                new_status=self.room_plan.status,
                                                value=self.room_id))

    def __del__(self):
        # DO NOT USE loguru here: https://github.com/Delgan/loguru/issues/712
        if self.config.console_log:
            print(f'{self.room_id} object has died')

    async def add_tag_status(self,
                             tag: str,
                             new_status: str,
                             external_time: str = "",
                             trigger_time: str = "",
                             value: str = "",
                             debug_log: int = 0):
        """Stores tag status and run check triggers

        @param str tag: Object Tag
        @param str new_status: new status for tag
        @param str external_time: time from asterisk or external service (if exist)
        @param str trigger_time: time from create trigger event after receive asterisk event (if exist)
        @param str value: Additional data
        @param int debug_log: for debugging
        @return: None
        """
        self.log.info(f' tag={tag} new status={new_status} value={value}')

        if tag not in self.tags_statuses:
            self.tags_statuses[tag] = {}

        if self.tags_statuses[tag].get(new_status) is None:
            self.tags_statuses[tag][new_status] = {
                "external_time": external_time,
                "trigger_time": trigger_time,
                "add_status_time": datetime.now().isoformat(),
                "value": value,
                "rewrite": []
            }
        else:
            row_rewrite = {
                "external_time": external_time,
                "trigger_time": trigger_time,
                "add_status_time": datetime.now().isoformat(),
                "value": value
            }
            self.tags_statuses[tag][new_status]["rewrite"].append(row_rewrite)

        if new_status == 'THIS_FOR_DEBUG':
            debug_log = random.randrange(0, 100000)
            self.log.info(f'debug_log={debug_log}')

        await self.check_trigger_room(debug_log)
        await self.check_trigger_bridges(debug_log)

        await asyncio.sleep(0)

    def check_tag_status(self, tag, status):
        """
        Given a tag and a status, check if the status is associated with tag in the object's tags_statuses dictionary

        @param tag - the tag to check
        @param status - the status to check
        @return True if the status is associated with the tag, False otherwise.
        """
        if tag not in self.tags_statuses:
            return False
        elif status not in self.tags_statuses[tag]:
            return False
        else:
            return True

    def get_first_time_tag_status(self, tag: str, status: str) -> Union[str, None]:
        if tag not in self.tags_statuses:
            self.log.warning(f'tag={tag} not found in tags_statuses')
            return None
        elif status not in self.tags_statuses[tag]:
            self.log.warning(f'status={status} not found in tags_statuses[{tag}]')
            return None
        else:
            tag_status = self.tags_statuses.get(tag, dict()).get(status, dict())
            time = tag_status.get('external_time')
            if time is None or time == '':
                time = tag_status.get('trigger_time')
            if time is None or time == '':
                time = tag_status.get('add_status_time')
            if time is None or time == '':
                self.log.error(f'Not time in tags_statuses[{tag}][{status}]')
                time = datetime.now().isoformat()

            return time

    async def bridge_termination_handler(self):
        """
        This is an asynchronous function that handles the termination of a bridge.

        @return None
        """
        if self.config.alive:
            for bridge in list(self.bridges.values()):
                await self.add_tag_status(tag=bridge.tag,
                                          new_status='stop',
                                          value='bridge_termination_handler')
                await bridge.chan_termination_handler()
                self.bridges.pop(bridge.tag)
                self.log.debug(f'remove bridge with tag={bridge.tag} from memory')
            self.log.debug(self.tags_statuses)

    async def start_room(self):
        """
        This is an asynchronous function that starts a room.
        It logs the message "start_room" and then adds a tag status with the given tag and new status 'ready'

        @return None
        """
        self.log.info('start_room')
        asyncio.create_task(self.add_tag_status(tag=self.tag, new_status='ready'))

    async def check_trigger_room(self, debug_log: int = 0):
        """
        This is an asynchronous function that checks if a trigger room is active.

        @return None
        """
        if debug_log > 0:
            self.log.debug(f'debug_log={debug_log}')

        for trigger in [trg for trg in self.room_plan.triggers if trg.action == 'terminate' and trg.active]:
            if trigger.trigger_status in self.tags_statuses.get(trigger.trigger_tag, []):
                trigger.active = False
                asyncio.create_task(self.add_tag_status(tag=self.tag, new_status='stop'))

    async def check_trigger_bridges(self, debug_log: int = 0):
        """
        Asynchronous method that checks the status of bridges and triggers.
        """
        if debug_log > 0:
            self.log.debug(f'debug_log={debug_log}')

        for bridge_plan in self.bridges_plan:
            if bridge_plan.tag in [bridge.tag for bridge in self.bridges.values()]:
                # check terminate trigger if bridge already exist
                for trigger in [trg for trg in bridge_plan.triggers if trg.action == 'terminate' and trg.active]:
                    # check match the status of the object being monitored by the trigger
                    if trigger.trigger_status in self.tags_statuses.get(trigger.trigger_tag, []):
                        trigger.active = False
                        asyncio.create_task(self.bridges[bridge_plan.tag].destroy_bridge())
            else:
                # check start trigger if bridge does not exist
                for trigger in [trg for trg in bridge_plan.triggers if trg.action == 'start' and trg.active]:
                    if trigger.trigger_status in self.tags_statuses.get(trigger.trigger_tag, []):
                        trigger.active = False
                        bridge = Bridge(asterisk_client=self.asterisk_client,
                                        config=self.config,
                                        room=self,
                                        bridge_plan=bridge_plan)
                        self.bridges[bridge.tag] = bridge
                        asyncio.create_task(bridge.start_bridge())

        for bridge in list(self.bridges.values()):
            if self.call_id != bridge.call_id:
                self.log.error('WTF')
            await bridge.check_trigger_chans(debug_log)

    async def trigger_event_handler(self, trigger_event: TriggerEvent):
        """
        This is an asynchronous function that handles a trigger event.
        It takes in a TriggerEvent object and adds the tag status to the database.

        @param trigger_event - a TriggerEvent object containing information about the event
        @return None (asynchronous)
        """
        asyncio.create_task(self.add_tag_status(trigger_event.tag,
                                                trigger_event.status,
                                                trigger_event.external_time,
                                                trigger_event.trigger_time,
                                                trigger_event.value))
