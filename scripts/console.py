import asyncio
import logging
import os
import sys
import warnings

import IPython
import nest_asyncio
from tortoise.context import TortoiseContext
from tortoise.warnings import TortoiseLoopSwitchWarning
from traitlets.config import Config

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.db.tortoise_config import TORTOISE_CONFIG
from app.models.blue_green_config import BlueGreenConfig
from app.models.product import Product
from app.models.scoring_profile import ScoringProfile
from app.models.user import User
from app.services.auth_service import AuthService

# Allow await in IPython's event loop
nest_asyncio.apply()
warnings.filterwarnings("ignore", category=TortoiseLoopSwitchWarning)

# Show executed SQL like Rails console
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logging.getLogger("tortoise.db_client").setLevel(logging.DEBUG)
# Suppress noise from other libs
for name in ("asyncio", "tortoise", "passlib", "urllib3", "httpx", "asyncpg"):
    logging.getLogger(name).setLevel(logging.WARNING)

_ctx = TortoiseContext()


async def _init():
    _ctx.__enter__()  # set contextvar in current task
    await _ctx.init(config=TORTOISE_CONFIG, _enable_global_fallback=True)
    print("[INFO] DB connected")


async def _close():
    await _ctx.close_connections()
    print("[INFO] DB closed")


loop = asyncio.get_event_loop()
loop.run_until_complete(_init())

namespace = {
    "User": User,
    "Product": Product,
    "ScoringProfile": ScoringProfile,
    "BlueGreenConfig": BlueGreenConfig,
    "AuthService": AuthService,
    "settings": settings,
    "asyncio": asyncio,
}

c = Config()
c.InteractiveShellApp.exec_lines = [
    "%autoawait asyncio",
    'print("-" * 50)',
    'print("NOVA AI CONSOLE READY")',
    'print("  await User.all()")',
    'print("  await User.get(id=1)")',
    "print(\"  await Product.filter(brand='Nike').limit(5)\")",
    'print("-" * 50)',
]
c.TerminalInteractiveShell.confirm_exit = False
c.TerminalInteractiveShell.sql_color = True


try:
    IPython.start_ipython(argv=[], user_ns=namespace, config=c)
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    loop.run_until_complete(_close())
