import logging

import extensions
from routes.security import read_token_claims

logger = logging.getLogger(__name__)


def get_current_user(request, offline=False):
    token = request.cookies.get("access_token")
    if not token:
        return None

    claims = read_token_claims(token)
    if not claims:
        return None
    user = {
        "id": claims["sub"],
        "email": claims.get("email"),
        "role": claims.get("role", "user"),
    }
    # Core analysis and optional AI enhancement can trust signed local claims.
    # Other routes refresh the user record when the online store is available,
    # preserving existing role and account-state behavior.
    if offline and claims.get("email") and claims.get("role"):
        return user

    supabase = extensions.supabase
    if supabase:
        try:
            result = supabase.table("users").select("id, email, role").eq("id", claims["sub"]).execute()
            if result.data:
                record = result.data[0]
                return {"id": record["id"], "email": record.get("email"), "role": record.get("role", "user")}
        except Exception:
            logger.info("Supabase user lookup unavailable; using signed token claims for this request.", exc_info=True)
    return user
