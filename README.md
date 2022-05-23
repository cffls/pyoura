
## PyOura

PyOura is a python client for [Oura](https://github.com/txpipe/oura).

## Usage

### Prerequisite

* Oura binary is installed on local machine. 
See installation instruction [here](https://txpipe.github.io/oura/installation/binary_release.html).
* An endpoint of a Cardano node.

### Start oura 

Assuming a cardano node's endpoint is available at "localhost:3001"

Save the code below to `start.py`
```python
from oura import start, Event

def handle_event(event):
    # Do anything in python
    print("New event!")
    print(event)

cardano_node_endpoint = "localhost:3001"
    
start(cardano_node_endpoint, 
      handler=handle_event, 
      events=[Event.Transaction, Event.RollBack],
      host="0.0.0.0",
      port=9000)
```

Start oura
```shell
python3 start.py
```

You will see logs from oura server like below:
```shell
Oura config:
 [[filters]]
type = "Selection"

[filters.check]
predicate = "variant_in"
argument = [ "Transaction", "RollBack",]

[source]
type = "N2N"
address = [ "Tcp", "localhost:3001",]
magic = "mainnet"

[sink]
type = "Webhook"
url = "http://0.0.0.0:9000/events"
timeout = 30000
error_policy = "Continue"
max_retries = 30
backoff_delay = 5000

Bottle v0.12.19 server starting up (using WSGIRefServer())...
Listening on http://0.0.0.0:9000/
Hit Ctrl-C to quit.

New event!
{'context': {'block_hash': None, 'block_number': None, 'slot': None, 'timestamp': None, 'tx_idx': None, 'tx_hash': None, 'input_idx': None, 'output_idx': None, 'output_address': None, 'certificate_idx': None}, 'roll_back': {'block_slot': 61717026, 'block_hash': '4f88997028098b769ded8df1eae38ec973896fe6aea2d765d9d382d21a9e2d48'}, 'fingerprint': None, 'variant': 'RollBack', 'timestamp': None}
127.0.0.1 - - [22/May/2022 22:22:29] "POST /events HTTP/1.1" 200 2
New event!
{'context': {'block_hash': '7e7c8d548066ab636312a28c818b22d2f3f13b5946b035d9c1236538def50ad8', 'block_number': 7281497, 'slot': 61716375, 'timestamp': 1653282666, 'tx_idx': 0, 'tx_hash': '0bf430455a5e0a4d736e4184d55ed948b73e0e5f9677ddb1f8850eec92e7f150', 'input_idx': None, 'output_idx': None, 'output_address': None, 'certificate_idx': None}, 'transaction': {'hash': '0bf430455a5e0a4d736e4184d55ed948b73e0e5f9677ddb1f8850eec92e7f150', 'fee': 214473, 'ttl': 61766353, 'validity_interval_start': None, 'network_id': None, 'input_count': 1, 'output_count': 3, 'mint_count': 1, 'total_output': 59785527, 'metadata': None, 'inputs': None, 'outputs': None, 'mint': None}, 'fingerprint': None, 'variant': 'Transaction', 'timestamp': 1653282666000}
127.0.0.1 - - [22/May/2022 22:22:32] "POST /events HTTP/1.1" 200 2
```

### Restart oura with a specific slot

Event handler can sometimes fail due to bugs or infra failures. In that case, we want to rerun or re-read events 
from a specific point in the chain. We can restart oura process by calling function `set_cursor` with a cursor object 
 (a unique identifier to a block).

```python
from oura import set_cursor, Cursor

slot = 61716365
block_hash_at_slot = "b7c92be36e0d3db13078913850cec630683e327ac42e3962f261791e979b7cf0"
start_from = Cursor(slot, block_hash_at_slot)
set_cursor(start_from, 
           host="0.0.0.0",
           port=9000)
```

`set_cursor` will restart oura and have it read from the specified point in the chain.

Sample output from oura server:

```shell
Restart oura from: {'slot': 61717072, 'block_hash': '94949f09d831e33cc183abd2a2dafe61a3d75c4aab3e9e25baa570d694cbcd03'}
127.0.0.1 - - [22/May/2022 22:40:14] "POST /restart HTTP/1.1" 200 2
{'context': {'block_hash': None, 'block_number': None, 'slot': None, 'timestamp': None, 'tx_idx': None, 'tx_hash': None, 'input_idx': None, 'output_idx': None, 'output_address': None, 'certificate_idx': None}, 'roll_back': {'block_slot': 61717072, 'block_hash': '94949f09d831e33cc183abd2a2dafe61a3d75c4aab3e9e25baa570d694cbcd03'}, 'fingerprint': None, 'variant': 'RollBack', 'timestamp': None}
```