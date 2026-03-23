from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from app.core.security import verify_admin_token

class CustomLimiterMiddleware(SlowAPIMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Do not bypass rate limit for login routes
        login_paths = ["/auth/login", "/auth/admin/login"]
        if any(request.url.path.endswith(p) for p in login_paths):
            return await super().dispatch(request, call_next)

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # verify_admin_token will raise HTTPException if invalid
                # but we just want to catch it and proceed normally if not an admin
                payload = verify_admin_token(token)
                if payload and payload.get("role") == "admin":
                    # Bypass rate limit
                    return await call_next(request)
            except Exception:
                pass
                
        return await super().dispatch(request, call_next)
