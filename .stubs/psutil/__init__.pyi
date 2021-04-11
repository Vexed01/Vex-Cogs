# THESE STUBS WERE MADE BY ME BECAUSE AUTO GENERATION
# 1) WILL GENERATE FOR CURRENT OS, NOT ALL OSES
# 2) AUTO GENERATION MAINLY DOESNT HAVE TYPEHINTS

from collections import namedtuple
from typing import Dict, Generator, List, Optional, TypedDict

from ._common import sdiskpart, sdiskusage, suser

LINUX: bool
WINDOWS: bool

# -------------------------------------------------------------------------------------------------
# these are NOT representive of the actual code as the namedtuped changes based on the os
# this cog uses three attributes - and they are supported on all OSes
# most of these are also in _common or the oses file so :awesome:
scputimes = namedtuple("scputimes", ["user", "idle", "system"])
scpufreq = namedtuple("scpufreq", ["current", "min", "max"])
svmem = namedtuple("svmem", ["total", "available", "percent", "used"])
sswap = namedtuple("sswap", ["total", "used", "free", "percent"])
shwtemp = namedtuple("shwtemp", ["label", "current", "high", "critical"])
sfan = namedtuple("sfan", ["label", "current"])

class ProcInfo(TypedDict):
    status: str
    username: str

class Process:
    info: ProcInfo

# -------------------------------------------------------------------------------------------------
# some of these can return others but for this cog will only return one thing due to args used
def cpu_percent(interval: bool = None, percpu: bool = False) -> List[float]: ...
def cpu_times(percpu: bool = False) -> scputimes: ...
def cpu_freq(percpu: bool = False) -> List[scpufreq]: ...
def cpu_count(logical: bool = True) -> int: ...
def boot_time() -> float: ...
def virtual_memory() -> svmem: ...
def swap_memory() -> sswap: ...
def sensors_temperatures(fahrenheit: bool = False) -> Dict[str, List[shwtemp]]: ...
def sensors_fans() -> Dict[str, List[sfan]]: ...
def users() -> List[suser]: ...
def disk_partitions(all: bool = False) -> List[sdiskpart]: ...
def disk_usage(path: str) -> sdiskusage: ...
def process_iter(
    attars: Optional[list] = None, ad_value=None
) -> Generator[Process, Process, Process]: ...
