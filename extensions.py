import logging

from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

from config import SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        # Bound optional history and legacy-user lookups when the network is down.
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
            SyncClientOptions(postgrest_client_timeout=2.0),
        )
    except Exception:
        logger.warning("Supabase is unavailable; analysis will continue without history.", exc_info=True)
else:
    logger.info("Supabase credentials are not configured; analysis history is disabled.")

latest_reports = {}
