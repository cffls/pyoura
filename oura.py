import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from tempfile import NamedTemporaryFile
from typing import List

import requests
import toml
from bottle import Bottle, run, request

__all__ = ["Event", "Cursor", "start", "set_cursor"]


class Event(Enum):
    """Oura events defined in https://txpipe.github.io/oura/reference/data_dictionary.html"""

    RollBack = 0
    Block = 1
    Transaction = 2
    TxInput = 3
    TxOutput = 4
    OutputAsset = 5
    Metadata = 6
    Mint = 7
    Collateral = 8
    PlutusScriptRef = 9
    StakeRegistration = 10
    StakeDeregistration = 11
    StakeDelegation = 12
    PoolRegistration = 13
    PoolRetirement = 14
    GenesisKeyDelegation = 15
    MoveInstantaneousRewardsCert = 16


@dataclass
class Cursor:
    slot: int
    block_hash: str

    def __str__(self):
        return f"{self.slot},{self.block_hash}"


def _build_oura_webhook_config(
    source_url,
    sink_url,
    network: str = "mainnet",
    events: List[Event] = None,
    timeout: int = 30000,
    error_policy: str = "Continue",
    max_retries: int = 30,
    backoff_delay: int = 5000,
) -> str:
    if not events:
        events = [e.name for e in Event]
    else:
        events = [e.name for e in events]

    config = {
        "source": {"type": "N2N", "address": ["Tcp", source_url], "magic": network},
        "sink": {
            "type": "Webhook",
            "url": sink_url,
            "timeout": timeout,
            "error_policy": error_policy,
            "max_retries": max_retries,
            "backoff_delay": backoff_delay,
        },
        "filters": [
            {
                "type": "Selection",
                "check": {"predicate": "variant_in", "argument": events},
            }
        ],
    }
    toml_config = toml.dumps(config)
    with NamedTemporaryFile("w", suffix=".toml", delete=False) as tmp_config:
        print("Oura config:\n", toml_config)
        tmp_config.write(toml_config)
    return tmp_config.name


def _check_oura_binary():
    if not shutil.which("oura"):
        raise Exception("Cannot find oura executable!")


def _start_oura_daemon(config_path: str, cursor: Cursor = None) -> subprocess.Popen:
    _check_oura_binary()
    cmd = ["oura", "daemon", "--config", config_path]
    if cursor:
        cmd += ["--cursor", str(cursor)]
    return subprocess.Popen(cmd)


app = Bottle()


def start(
    source_url,
    handler=lambda x: print(x),
    tip: Cursor = None,
    host: str = "0.0.0.0",
    port: int = 9000,
    network: str = "mainnet",
    events: List[Event] = None,
    timeout: int = 30000,
    error_policy: str = "Continue",
    max_retries: int = 30,
    backoff_delay: int = 5000,
):
    config = _build_oura_webhook_config(
        source_url,
        sink_url=f"http://{host}:{port}/events",
        events=events,
        network=network,
        timeout=timeout,
        error_policy=error_policy,
        max_retries=max_retries,
        backoff_delay=backoff_delay,
    )
    app.config = config
    app.oura_daemon = _start_oura_daemon(config, tip)

    @app.post("/events")
    def event_handler():
        handler(request.json)
        return "ok"

    @app.post("/restart")
    def restart():
        print(f"Restart oura from: {request.json}")
        tip = Cursor(request.json["slot"], request.json["block_hash"])
        app.oura_daemon.terminate()
        app.oura_daemon = _start_oura_daemon(app.config, tip)
        return "ok"

    run(app, host=host, port=port)


def set_cursor(cursor: Cursor, host: str = "0.0.0.0", port: int = 9000):
    requests.post(
        f"http://{host}:{port}/restart",
        json={"slot": cursor.slot, "block_hash": cursor.block_hash},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
