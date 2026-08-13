# core/middleware.py
import logging

from django.conf import settings
from django.db import connection
from django.http import Http404
from django_tenants.utils import get_tenant_model

from core.models import Domain

logger = logging.getLogger(__name__)


class DomainType:
    ROOT = "ROOT"
    BRIDGE = "BRIDGE"
    TENANT = "TENANT"


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].strip().lower()

        # 1. Determine Domain Type
        public_domains = [getattr(settings, "PUBLIC_DOMAIN", "")]
        bridge_domains = [getattr(settings, "BRIDGE_DOMAIN", "")]
        
        if host in public_domains:
            request.domain_type = DomainType.ROOT
        elif host in bridge_domains:
            request.domain_type = DomainType.BRIDGE
        else:
            request.domain_type = DomainType.TENANT

        # 2. Resolve Tenant
        tenant = None
        try:
            domain_obj = Domain.objects.select_related("tenant").get(domain=host)
            tenant = domain_obj.tenant
        except Domain.DoesNotExist:
            if host in ["localhost", "127.0.0.1"] and settings.DEBUG:
                try:
                    TenantModel = get_tenant_model()
                    tenant = TenantModel.objects.get(schema_name="public")
                except TenantModel.DoesNotExist:
                    pass

        if tenant:
            request.tenant = tenant
            connection.set_tenant(request.tenant)
            return self.get_response(request)

        logger.warning(f"Access Denied: Unmapped domain route detected for Host '{host}'")
        raise Http404("Tenant or domain space not found.")