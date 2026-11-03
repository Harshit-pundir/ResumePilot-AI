from extensions import supabase
from routes.security import read_token


def get_current_user(request):
    token = request.cookies.get("access_token")
    if not token:
        return None

    user_id = read_token(token)
    if not user_id:
        return None

    result = supabase.table("users").select("id, email, role").eq("id", user_id).execute()
    if not result.data:
        return None
    user = result.data[0]
    return {"id": user["id"], "email": user["email"], "role": user["role"]}
