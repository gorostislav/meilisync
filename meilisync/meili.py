import functools
from typing import List

from loguru import logger
from meilisearch_python_async import Client

from meilisync.enums import EventType
from meilisync.schemas import Event
from meilisync.settings import MeiliSearch, Sync


class Meili:
    def __init__(self, debug: bool, meilisearch: MeiliSearch, sync: List[Sync]):
        self.client = Client(
            meilisearch.api_url,
            meilisearch.api_key,
        )
        self.sync = sync
        self.debug = debug

    @functools.lru_cache()
    def _get_sync(self, table: str):
        for sync in self.sync:
            if sync.table == table:
                return sync

    async def add_full_data(self, index: str, data: list):
        return await self.client.index(index).add_documents(data)

    async def handle_event(self, event: Event):
        if self.debug:
            logger.debug(event)
        table = event.table
        sync = self._get_sync(table)
        if not sync:
            return
        index = self.client.index(sync.index or table)
        if event.type == EventType.create:
            return await index.add_documents(
                [event.mapping_data(sync.fields_mapping)], primary_key=sync.pk
            )
        elif event.type == EventType.update:
            return await index.update_documents(
                [event.mapping_data(sync.fields_mapping)], primary_key=sync.pk
            )
        elif event.type == EventType.delete:
            return await index.delete_documents([str(getattr(event.data, sync.pk))])