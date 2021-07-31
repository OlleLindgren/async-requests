# async-requests

A library for doing GET requests asyncronously

## Dependencies

```
python>=3.7
asyncio
aiohttp
```

## Install

`pip install git+https://github.com/OlleLindgren/async-requests@v0.1.2`

## Usage: Asyncronous GET requests

```python
from asyncrequests import Forwarder, forward

# Forward requests
urls: Iterable # Put the urls you want to get in here

# Quick and dirty
results = forward(urls) # Generator with results of requests

# Forwarder object gives a bit more control
fwd = Forwarder(
    max_freq = 10.0,  # Requests / second
    max_attempts = 2, # Attempts / request url
    batch_size = 20   # Size of each batch
)
# Result is given in batches
batches = fwd.collect_at_freq(urls)
# Batches are easily converted to a generator that can then be persistent across all urls
def _result_generator():
    for batch in batches:
        for item in batch:
            yield item
results = _result_generator() # Generator with results of requests

# The contents of results is sorted in the order that the requests came back.
# However, this is not necessarily the same order as the urls. Therefore, I'm
# returning a dictionary in the following format: 
#   {url: {"success": response.status_code==200, "json": response.json()}}
# We can unpack it by doing:

first_result = next(result)
url, get_result = list(firs_result.items())[0]
success = get_result['success']  # same as response.status_code
result_json = get_result['json'] # same as response.json()
```
