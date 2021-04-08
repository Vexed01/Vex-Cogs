import asyncio
import datetime
from typing import Dict, List, Union

import psutil
from redbot.core.utils.chat_formatting import box as cf_box
from redbot.core.utils.chat_formatting import humanize_number, humanize_timedelta
from tabulate import tabulate


def box(text: str):
    """Box up text as toml. May return over 2k chars"""
    return cf_box(text, "toml")


def _hum(num: Union[int, float]):
    """Round a number, then humanize."""
    return humanize_number(round(num))


def _hum_mb(bytes: Union[int, float]):
    """Convert to MBs, round, then humanize."""
    mb = bytes / 1048576
    return _hum(mb)


def _hum_gb(bytes: Union[int, float]):
    """Convert to GBs, round, then humanize."""
    mb = bytes / 1073741824
    return _hum(mb)


def _up_since():
    now = datetime.datetime.utcnow().timestamp()
    return now - psutil.boot_time()


async def get_cpu():
    """Get CPU metrics"""
    psutil.cpu_percent()
    await asyncio.sleep(1)
    percent = psutil.cpu_percent(percpu=True)
    time = psutil.cpu_times()
    freq = psutil.cpu_freq(percpu=True)
    cores = psutil.cpu_count()

    if psutil.LINUX:
        data = {"percent": "", "freq": "", "freq_note": "", "time": ""}
        for i in range(cores):
            data["percent"] += f"[Core {i}] {percent[i]} %\n"
            ghz = round((freq[i].current / 1000), 2)
            data["freq"] += f"[Core {i}] {ghz} GHz\n"
    else:
        data = {"percent": "", "freq": "", "freq_note": " (nominal)", "time": ""}
        for i in range(cores):
            data[
                "percent"
            ] += f"[Core {i}] {percent[i]} % \n"  # keep extra space here, for special case, tabulate removes it
        ghz = round((freq[0].current / 1000), 2)
        data["freq"] = f"{ghz} GHz\n"  # blame windows

    data["time"] += f"[Idle]   {_hum(time.idle)} seconds\n"
    data["time"] += f"[User]   {_hum(time.user)} seconds\n"
    data["time"] += f"[System] {_hum(time.system)} seconds\n"
    data["time"] += f"[Uptime] {_hum(_up_since())} seconds\n"

    return data


async def get_mem():
    """Get memory metrics"""
    physical = psutil.virtual_memory()
    swap = psutil.swap_memory()

    data = {"physical": "", "swap": ""}

    data["physical"] += f"[Percent]   {physical.percent} %\n"
    data["physical"] += f"[Used]      {_hum_mb(physical.used)} MB\n"
    data["physical"] += f"[Available] {_hum_mb(physical.available)} MB\n"
    data["physical"] += f"[Total]     {_hum_mb(physical.total)} MB\n"

    data["swap"] += f"[Percent]   {swap.percent} %\n"
    data["swap"] += f"[Used]      {_hum_mb(swap.used)} MB\n"
    data["swap"] += f"[Available] {_hum_mb(swap.free)} MB\n"
    data["swap"] += f"[Total]     {_hum_mb(swap.total)} MB\n"

    return data


async def get_sensors(fahrenheit: bool):
    """Get metrics from sensors"""
    temp = psutil.sensors_temperatures(fahrenheit)
    fans = psutil.sensors_fans()

    data = {"temp": "", "fans": ""}

    unit = "°F" if fahrenheit else "°C"

    t_data = []
    for k, v in temp.items():
        for item in v:
            item: psutil._common.shwtemp
            name = item.label or k
            t_data.append([f"[{name}]", f"{item.current} {unit}"])
    data["temp"] = tabulate(t_data, tablefmt="plain") or "No temperature sensors found"

    t_data = []
    for k, v in fans.items():
        for item in v:
            item: psutil._common.sfan
            name = item.label or k
            t_data.append([f"[{name}]", f"{item.current} RPM"])
    data["fans"] = tabulate(t_data, tablefmt="plain") or "No fan sensors found"

    return data


async def get_users(embed: bool):
    """Get users connected"""
    users: List[psutil._common.suser] = psutil.users()

    e = "`" if embed else ""

    data = {}

    for user in users:
        data[f"{e}{user.name}{e}"] = "[Terminal]  {}\n".format(user.terminal or "Unknown")
        started = datetime.datetime.fromtimestamp(user.started).strftime("%Y-%m-%d at %H:%M:%S")
        data[f"{e}{user.name}{e}"] += f"[Started]   {started}\n"
        if not psutil.WINDOWS:
            data[f"{e}{user.name}{e}"] += f"[PID]       {user.pid}"

    return data


async def get_disk(embed: bool):
    """Get disk info"""
    partitions = psutil.disk_partitions()
    partition_data: Dict[str, List[Union[psutil._common.sdiskpart, psutil._common.sdiskusage]]] = {}
    # that type hint was a waste of time...

    for partition in partitions:
        try:
            partition_data[partition.device] = [partition, psutil.disk_usage(partition.mountpoint)]
        except Exception:
            continue

    e = "`" if embed else ""

    data = {}

    for k, v in partition_data.items():
        total_avaliable = f"{_hum_gb(v[1].total)} GB" if v[1].total > 1073741824 else f"{_hum_mb(v[1].total)} MB"
        data[f"{e}{k}{e}"] = f"[Usage]       {v[1].percent} %\n"
        data[f"{e}{k}{e}"] += f"[Total]       {total_avaliable}\n"
        data[f"{e}{k}{e}"] += f"[Filesystem]  {v[0].fstype}\n"
        data[f"{e}{k}{e}"] += f"[Mount point] {v[0].mountpoint}\n"

    return data


async def get_proc():
    """Get process info"""
    processes = psutil.process_iter(["status", "username"])
    status = {"sleeping": 0, "idle": 0, "running": 0, "stopped": 0}

    for process in processes:
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


async def get_uptime():
    """Get uptime info"""
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())

    friendly_boot_time = boot_time.strftime("%b %d, %H:%M:%S UTC")
    friendly_up_for = humanize_timedelta(timedelta=datetime.datetime.utcnow() - boot_time)

    data = {"uptime": ""}

    data["uptime"] += f"[Boot time] {friendly_boot_time}\n"
    data["uptime"] += f"[Up for]    {friendly_up_for}\n"

    return data
