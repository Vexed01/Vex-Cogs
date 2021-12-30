import os
import subprocess
import time

import requests
from dotenv import load_dotenv
from redbot import __version__ as red_str_ver

load_dotenv(".env")

token = os.environ.get("DISCORD_BOT_TOKEN")

python_version = subprocess.check_output(["python", "-V"]).decode("utf-8")

print(f"== Starting Red {red_str_ver} with {python_version}")

proc = subprocess.Popen(
    f"redbot --no-instance --no-prompt --prefix ! --token {token} --rpc",
    # stdout=subprocess.PIPE,
    # want to let errors go through to logs
)

# let Red boot up
time.sleep(10)

# not compatible with dpy 1.x
# ["buttonpoll", "ghissues"]

cogs = [
    "aliases",
    "anotherpingcog",
    "beautify",
    "betteruptime",
    "caseinsensitive",
    "cmdlog",
    "covidgraph",
    "github",
    "googletrends",
    "madtranslate",
    "stattrack",
    "status",
    "system",
    "timechannel",
    "wol",
    #
    "buttonpoll",
]

print(f"== Attempting to load {len(cogs)} cogs...")

payload = {
    "method": "GET_METHODS",
    # "params": [cogs],
    "jsonrpc": "2.0",
    "id": 0,
}

resp = requests.post("http://localhost:6133/", json=payload)

print("Stopping Red")
proc.terminate()

print(resp.text)
print(resp)
print(resp.json())

# TRY TO FIND A WEBSOCKETS CLIENT

print("== done")
