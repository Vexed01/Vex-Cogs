from __future__ import annotations

from typing import TypedDict


class Chart(TypedDict):
    title: str
    ylabel: str
    valid_metrics: list[str]
    do_average: bool
    show_total: bool
    more_options: bool
    status_colours: bool


ALL_CHARTS: dict[str, Chart] = {
    "latency": {
        "title": "Latency",
        "ylabel": "Latency (ms)",
        "valid_metrics": ["ping"],
        "do_average": False,
        "show_total": False,
        "more_options": False,
        "status_colours": False,
    },
    "looptime": {
        "title": "Loop Time",
        "ylabel": "Loop Time (seconds)",
        "valid_metrics": ["loop_time_s"],
        "do_average": False,
        "show_total": False,
        "more_options": False,
        "status_colours": False,
    },
    "commands": {
        "title": "Commands per minute",
        "ylabel": "Commands per minute",
        "valid_metrics": ["command_count"],
        "do_average": True,
        "show_total": True,
        "more_options": False,
        "status_colours": False,
    },
    "messages": {
        "title": "Messages per minute",
        "ylabel": "Messages per minute",
        "valid_metrics": ["message_count"],
        "do_average": True,
        "show_total": True,
        "more_options": False,
        "status_colours": False,
    },
    "servers": {
        "title": "Server count",
        "ylabel": "Server count",
        "valid_metrics": ["guilds"],
        "do_average": False,
        "show_total": False,
        "more_options": False,
        "status_colours": False,
    },
    "status": {
        "title": "User status",
        "ylabel": "User count",
        "valid_metrics": ["status_online", "status_idle", "status_offline", "status_dnd"],
        "do_average": False,
        "show_total": False,
        "more_options": False,
        "status_colours": True,
    },
    "users": {
        "title": "User count",
        "ylabel": "User count",
        "valid_metrics": ["users_total", "users_humans", "users_bots", "users_unique"],
        "do_average": False,
        "show_total": False,
        "more_options": False,
        "status_colours": False,
    },
    "channels": {
        "title": "Channels",
        "ylabel": "Channel count",
        "valid_metrics": [
            "channels_total",
            "channels_text",
            "channels_voice",
            "channels_cat",
            "channels_stage",
        ],
        "do_average": False,
        "show_total": False,
        "more_options": False,
        "status_colours": False,
    },
    "cpu": {
        "title": "CPU Usage",
        "ylabel": "CPU Usage (%)",
        "valid_metrics": ["sys_cpu"],
        "do_average": False,
        "show_total": False,
        "more_options": False,
        "status_colours": False,
    },
    "mem": {
        "title": "Memory Usage",
        "ylabel": "Memory Usage (%)",
        "valid_metrics": ["sys_mem"],
        "do_average": False,
        "show_total": False,
        "more_options": False,
        "status_colours": False,
    },
}


TRACE_FRIENDLY_NAMES = {
    "ping": "Latency",
    "loop_time_s": "Loop time",
    "users_unique": "Unique",
    "users_total": "Total",
    "users_humans": "Humans",
    "users_bots": "Bots",
    "guilds": "Servers",
    "channels_total": "Total",
    "channels_text": "Text",
    "channels_voice": "Voice",
    "channels_stage": "Stage",
    "channels_cat": "Categories",
    "sys_mem": "Memory usage",
    "sys_cpu": "CPU Usage",
    "command_count": "Commands",
    "message_count": "Messages",
    "status_online": "Online",
    "status_idle": "Idle",
    "status_offline": "Offline",
    "status_dnd": "DnD",
}
