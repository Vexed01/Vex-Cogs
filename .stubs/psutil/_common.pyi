from collections import namedtuple

sdiskpart = namedtuple(
    "sdiskpart", ["device", "mountpoint", "fstype", "opts", "maxfile", "maxpath"]
)
sdiskusage = namedtuple("sdiskusage", ["total", "used", "free", "percent"])
suser = namedtuple("suser", ["name", "terminal", "host", "started", "pid"])
