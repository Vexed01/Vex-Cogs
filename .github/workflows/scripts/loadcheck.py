import os
import subprocess
import time

from dotenv import load_dotenv

load_dotenv(".env")

token = os.environ.get("DISCORD_BOT_TOKEN")

proc = subprocess.Popen(
    f"redbot --no-instance --no-prompt --prefix ! --token {token} --rpc",
    # stdout=subprocess.PIPE,
    # want to let errors go through to logs
)

# let Red boot up
time.sleep(10)

cogs = ["aliases", "anotherpingcog", "beautify", "betteruptime", "caseinsensitive", "cmdlog"]

print("done")
