import time
import datetime
import asyncio
from typing import Iterable, List, Tuple
import aiohttp
from queue import Queue
from collections import Counter

# Windows-specifics!
# asyncio has some problem with event loops that only happens on Windows.
# As suggested by some dude on the internet, I shall set the proper event loop policy!

# https://stackoverflow.com/questions/45600579/asyncio-event-loop-is-closed-when-getting-loop

import os
if os.name=='nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# End of Windows specifics

class Forwarder:

    max_freq: float                     # Max requests per second
    last_call: datetime.datetime        # Time when last call was made
    last_slot_given: datetime.datetime  # Last time slot given
    min_dt: datetime.timedelta          # Time between calls
    attempts: Counter                   # Number of attempts for each url
    max_attempts: int                   # Max number of attempts for any given url
    queue: Queue                        # Queue of urls and time slots to get requests from them

    def __init__(
        self, 
        max_freq: float=0.0, 
        max_attempts: int=2, 
        batch_size: int=20, # Results of collect_at_freq is returned in batches of size batch_size
        ) -> None:

        # Max frequency of requests. Unlimited if 0.0
        self.max_freq = max_freq
        # Max attempts for each url. Unlimited if 0
        self.max_attempts = max_attempts
        self.batch_size = batch_size

        # Time of last call (request)
        self.last_call = datetime.datetime.now()
        self.last_slot_given = datetime.datetime.now()
        # Number of attempts for each url
        self.attempts = Counter()
        # Queue of urls to process
        self.queue = Queue()

        # Minimum time between requests
        self.min_dt = datetime.timedelta(seconds = 1.0/max_freq if max_freq > 0.0 else 0.0)

        print(f'min dt={self.min_dt}, max freq={self.max_freq}')

    def iter_urls(self) -> Tuple[str, datetime.datetime]:
        while not self.queue.empty():
            yield self.queue.get()

    def process_queue(self) -> List[dict]:
        return asyncio.run(self.forward_at_freq(self.iter_urls()))

    def get_time_slot(self):
        t_slot = self.last_slot_given+self.min_dt
        self.last_slot_given = t_slot
        return t_slot

    def enqueue(self, url):
        # Get new time slot
        t_slot = self.get_time_slot()
        # Add to queue with time slot
        self.queue.put((url, t_slot))

    def collect_at_freq(self, urls) -> Iterable[List[dict]]:
        # Get urls asyncronosly. 
        # Returns a generator of batches with results.
        # Batches will contain batch_size urls, 

        for i, url in enumerate(urls):
            self.enqueue(url)

            # Batch formed; pause queueing and process batch
            if i % self.batch_size == 0:
                yield self.process_queue()
        
        # Process remainder of batch, if any
        yield self.process_queue()

    async def forward_at_freq(self, urls: Iterable[Tuple[str, datetime.datetime]]) -> list:
        async with aiohttp.ClientSession() as session:
            result = await asyncio.gather(*[
                self.forward_request_async(url, session, t_slot) 
                for url, t_slot in urls])
        return result

    async def forward_request_async(self, url: str, session: aiohttp.ClientSession, t_slot: datetime.datetime) -> dict:
        # Process a single request

        # If too early, wait until t_slot
        _t = datetime.datetime.now()
        _dt = t_slot - _t
        if _dt > datetime.timedelta(microseconds=0):
            time.sleep(_dt.microseconds/1e6)

        # Record time of call as last_call done by this instance
        self.last_call = datetime.datetime.now()

        success = False
        try:
            async with session.get(url=url) as response:
                assert response.status==200
                result = await response.json()
                success = response.status==200
        except:
            # 1 more attempt was made to reach this url
            self.attempts[url] += 1

            # If we can do more attempts, find a new time slot and queue it again
            if self.attempts[url] < self.max_attempts:
                self.enqueue(url)
            result = []
        
        return {url: {"json": result, "success": success}}

def forward(urls):
    # Quickly make async requests for a bunch of urls

    # Make forwarder object
    fwd = Forwarder()

    # Get batch generator
    batches = fwd.collect_at_freq(urls)

    # Convert batch generator to full result generator
    def _result_generator():
        for batch in batches:
            for item in batch:
                yield item

    return _result_generator()
