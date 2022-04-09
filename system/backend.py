from __future__ import annotations

import asyncio
import datetime
from typing import TypedDict

import psutil
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import box as cf_box
from redbot.core.utils.chat_formatting import humanize_number, humanize_timedelta, pagify
from tabulate import tabulate

from .vexutils.chat import humanize_bytes


def box(text: str) -> str:
    """Box up text as toml. Will not return more than 1024 chars (embed value limit)"""
    if len(text) > 1010:
        text = list(pagify(text, page_length=1024, shorten_by=12))[0]
        text += "\n..."
    return cf_box(text, "toml")


def up_for() -> float:
    now = datetime.datetime.now().timestamp()
    return now - psutil.boot_time()


def _hum(num: int | float) -> str:
    """Round a number, then humanize."""
    return humanize_number(round(num))


async def get_cpu() -> dict[str, str]:
    """Get CPU metrics"""
    psutil.cpu_percent()
    await asyncio.sleep(1)
    percent = psutil.cpu_percent(percpu=True)
    time = psutil.cpu_times()
    try:
        freq = psutil.cpu_freq(percpu=True)
    except NotImplementedError:  # happens on WSL
        freq = []
    cores = psutil.cpu_count()

    # freq could be [] because of WSL totally failing, and some other systems seem to give no
    # frequency data at all.

    if psutil.LINUX:
        do_frequ = len(freq) == cores
        data = {"percent": "", "freq": "", "freq_note": "", "time": ""}
        for i in range(cores):
            data["percent"] += f"[Core {i}] {percent[i]} %\n"
            if do_frequ:
                ghz = round((freq[i].current / 1000), 2)
                data["freq"] += f"[Core {i}] {ghz} GHz\n"
    else:
        do_frequ = len(freq) == 1
        data = {"percent": "", "freq": "", "freq_note": " (nominal)", "time": ""}
        for i in range(cores):
            data[
                "percent"
            ] += f"[Core {i}] {percent[i]} % \n"  # keep extra space here, for special case,
            # tabulate removes it
        if freq:
            ghz = round((freq[0].current / 1000), 2)
            data["freq"] = f"{ghz} GHz\n"  # blame windows

    if not do_frequ:
        data["freq"] = "Not available"

    data["time"] += f"[Idle]   {_hum(time.idle)} seconds\n"
    data["time"] += f"[User]   {_hum(time.user)} seconds\n"
    data["time"] += f"[System] {_hum(time.system)} seconds\n"
    data["time"] += f"[Uptime] {_hum(up_for())} seconds\n"

    return data


def get_mem() -> dict[str, str]:
    """Get memory metrics"""
    physical = psutil.virtual_memory()
    swap = psutil.swap_memory()

    data = {"physical": "", "swap": ""}

    data["physical"] += f"[Percent]   {physical.percent} %\n"
    data["physical"] += f"[Used]      {humanize_bytes(physical.used, 2)}\n"
    data["physical"] += f"[Available] {humanize_bytes(physical.available, 2)}\n"
    data["physical"] += f"[Total]     {humanize_bytes(physical.total, 2)}\n"

    data["swap"] += f"[Percent]   {swap.percent} %\n"
    data["swap"] += f"[Used]      {humanize_bytes(swap.used, 2)}\n"
    data["swap"] += f"[Available] {humanize_bytes(swap.free, 2)}\n"
    data["swap"] += f"[Total]     {humanize_bytes(swap.total, 2)}\n"

    return data


def get_sensors(fahrenheit: bool) -> dict[str, str]:
    """Get metrics from sensors"""
    temp = psutil.sensors_temperatures(fahrenheit)
    fans = psutil.sensors_fans()

    data = {"temp": "", "fans": ""}

    unit = "°F" if fahrenheit else "°C"

    t_data = []
    for t_k, t_v in temp.items():
        for t_item in t_v:
            name = t_item.label or t_k
            t_data.append([f"[{name}]", f"{t_item.current} {unit}"])
    data["temp"] = tabulate(t_data, tablefmt="plain") or "No temperature sensors found"

    f_data = []
    for f_k, f_v in fans.items():
        for f_item in f_v:
            name = f_item.label or f_k
            f_data.append([f"[{name}]", f"{f_item.current} RPM"])
    data["fans"] = tabulate(f_data, tablefmt="plain") or "No fan sensors found"

    return data


def get_users() -> dict[str, str]:
    """Get users connected"""
    users: list[psutil._common.suser] = psutil.users()

    data = {}

    for user in users:
        data[f"`{user.name}`"] = "[Terminal]  {}\n".format(user.terminal or "Unknown")
        started = datetime.datetime.fromtimestamp(user.started).strftime("%Y-%m-%d at %H:%M:%S")
        data[f"`{user.name}`"] += f"[Started]   {started}\n"
        if not psutil.WINDOWS:
            data[f"`{user.name}`"] += f"[PID]       {user.pid}"

    return data


class PartitionData(TypedDict):
    part: psutil._common.sdiskpart
    usage: psutil._common.sdiskusage


def get_disk() -> dict[str, str]:
    """Get disk info"""
    partitions = psutil.disk_partitions()
    partition_data: dict[str, PartitionData] = {}
    # that type hint was a waste of time...

    for partition in partitions:
        try:
            partition_data[partition.device] = {
                "part": partition,
                "usage": psutil.disk_usage(partition.mountpoint),
            }
        except Exception:
            continue

    data = {}

    for k, v in partition_data.items():
        total_avaliable = (
            f"{humanize_bytes(v['usage'].total)}"
            if v["usage"].total > 1073741824
            else f"{humanize_bytes(v['usage'].total)}"
        )
        data[f"`{k}`"] = f"[Usage]       {v['usage'].percent} %\n"
        data[f"`{k}`"] += f"[Total]       {total_avaliable}\n"
        data[f"`{k}`"] += f"[Filesystem]  {v['part'].fstype}\n"
        data[f"`{k}`"] += f"[Mount point] {v['part'].mountpoint}\n"

    return data


async def get_proc() -> dict[str, str]:
    """Get process info"""
    processes = psutil.process_iter(["status", "username"])
    status = {"sleeping": 0, "idle": 0, "running": 0, "stopped": 0}

    async for process in AsyncIter(processes):  # v slow on windows
        try:
            status[process.info["status"]] += 1
        except KeyError:
            continue

    sleeping = status["sleeping"]
    idle = status["idle"]
    running = status["running"]
    stopped = status["stopped"]
    total = sleeping + idle + running + stopped

    data = {"statuses": f"[Running]  {running}\n"}
    if psutil.WINDOWS:
        data["statuses"] += f"[Stopped]  {stopped}\n"
        data["statuses"] += f"[Total]    {total}\n"
    else:
        data["statuses"] += f"[Idle]     {idle}\n"
        data["statuses"] += f"[Sleeping] {sleeping}\n"
        if status["stopped"]:  # want to keep it at 4 rows
            data["statuses"] += f"[Stopped]  {stopped}\n"
        else:
            data["statuses"] += f"[Total]    {total}\n"

    return data


def get_net() -> dict[str, str]:
    """Get network stats. May have reset from zero at some point."""
    net = psutil.net_io_counters()

    data = {"counters": ""}
    data["counters"] += f"[Bytes sent]   {humanize_bytes(net.bytes_sent)}\n"
    data["counters"] += f"[Bytes recv]   {humanize_bytes(net.bytes_recv)}\n"
    data["counters"] += f"[Packets sent] {net.packets_sent}\n"
    data["counters"] += f"[Packets recv] {net.packets_recv}\n"

    return data


def get_uptime() -> dict[str, str]:
    """Get uptime info"""
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())

    tz = datetime.datetime.now().astimezone().tzinfo
    # boot_time is naive
    friendly_boot_time = boot_time.strftime(f"%b %d, %H:%M:%S {tz}")
    friendly_up_for = humanize_timedelta(timedelta=datetime.datetime.now() - boot_time)

    data = {"uptime": ""}

    data["uptime"] += f"[Boot time] {friendly_boot_time}\n"
    data["uptime"] += f"[Up for]    {friendly_up_for}\n"

    return data


async def get_red() -> dict[str, str]:
    """Get info for Red's process."""
    p = psutil.Process()

    p.cpu_percent()
    await asyncio.sleep(1)

    with p.oneshot():
        cpu = p.cpu_percent()
        phys_mem_pc = p.memory_percent("rss")
        phys_mem = p.memory_info().rss

        if psutil.LINUX:
            swap_mem_pc = p.memory_percent("swap")
            swap_mem = p.memory_full_info().swap
        else:
            swap_mem_pc = 0
            swap_mem = 0

    data = {"red": ""}

    data["red"] += f"[Process ID]   {p.pid}\n"
    data["red"] += f"[CPU Usage]    {cpu} %\n"
    data["red"] += f"[Physical mem] {round(phys_mem_pc, 2)} %\n"
    data["red"] += f"               {humanize_bytes(phys_mem, 1)}\n"
    if psutil.LINUX:
        data["red"] += f"[SWAP mem]     {round(swap_mem_pc, 2)} %\n"
        data["red"] += f"               {humanize_bytes(swap_mem, 1)}\n"

    return data
