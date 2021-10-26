from typing import TYPE_CHECKING, Optional

from redbot.core.bot import Red

from .chat import humanize_bytes, inline_hum_list
from .meta import format_help, format_info, out_of_date_check
from .sentry import SentryHelper as _SentryHelper
from .version import __version__

# if importlib.reload is ran, we don't want to re-initiate & overwrite SentryHelper - importlib
# keeps global variables
# to reiterate: SENTRY IS OPT-IN
if TYPE_CHECKING:
    sentryhelper = _SentryHelper()
    bot: Optional[Red] = None
else:
    try:
        sentryhelper
    except NameError:
        sentryhelper = _SentryHelper()
        bot = None
