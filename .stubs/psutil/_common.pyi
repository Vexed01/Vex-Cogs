from collections import namedtuple

sdiskpart = namedtuple(
    "sdiskpart", ["device", "mountpoint", "fstype", "opts", "maxfile", "maxpath"]
)
sdiskusage = namedtuple("sdiskusage", ["total", "used", "free", "percent"])
suser = namedtuple("suser", ["name", "terminal", "host", "started", "pid"])
snetio = namedtuple(
    "snetio",
    [
        "bytes_sent",
        "bytes_recv",
        "packets_sent",
        "packets_recv",
        "errin",
        "errout",
        "dropin",
        "dropout",
    ],
)
