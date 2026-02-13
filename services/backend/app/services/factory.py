"""Service factory for swapping real/demo ACAPyService.

Reads USE_DEMO environment variable to determine which service to instantiate.
"""

import os
from typing import Optional


def get_acapy_service(admin_url: Optional[str] = None, tenant_id: str = "default", tenant_token: Optional[str] = None):
    """Get ACAPyService instance based on USE_DEMO env var.

    Returns DemoACAPyService when USE_DEMO=true, else real ACAPyService.
    """
    use_demo = os.getenv("USE_DEMO", "false").lower() in ("true", "1", "yes")

    if use_demo:
        from app.services.demo_acapy import DemoACAPyService
        return DemoACAPyService(admin_url=admin_url, tenant_id=tenant_id, tenant_token=tenant_token)
    else:
        from app.services.acapy import ACAPyService
        return ACAPyService(admin_url=admin_url, tenant_id=tenant_id, tenant_token=tenant_token)
