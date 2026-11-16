import logging

from djoser import email

logger = logging.getLogger(__name__)


import logging

logger = logging.getLogger(__name__)




from urllib.parse import urlparse


class TenantRoleBasedPasswordResetEmail(email.PasswordResetEmail):
    template_name = "email/tenant_password_reset.html"

    def get_context_data(self):
        context = super().get_context_data()
        request = getattr(self, "request", None) or context.get("request")
        uid = context.get("uid")
        token = context.get("token")

        base_url = getattr(request, "reset_base_url", None) or getattr(
            getattr(request, "_request", None), "reset_base_url", None
        )

        if base_url:
            parsed = urlparse(base_url.rstrip("/"))
            client_path = parsed.path.lstrip("/")  

            context["protocol"] = parsed.scheme or "http"  
            context["domain"] = parsed.netloc              
            context["url"] = (
                f"{client_path}/{uid}/{token}" if client_path else f"{uid}/{token}"
            )

        return context



