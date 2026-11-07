"""The business profile the advisor collects. Every recommendation is a pure function of this."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Need = Literal[
    "internet",        # primary broadband for the premises
    "backup_internet", # failover when the main link drops
    "mobile_lines",    # business SIMs
    "payments",        # POS / billing / UPI
    "messaging",       # WhatsApp / SMS to customers
    "email",           # cloud email and office suite
    "backup",          # cloud data backup
    "security",        # endpoint / firewall
    "cctv",
    "wifi",            # managed / guest Wi-Fi
    "website",
    "telephony",       # IVR / business phone lines
    "toll_free",
    "static_ip",
    "multi_site_mgmt", # SD-WAN
    "iot",             # machine monitoring
    "fleet",           # vehicle tracking
    "dedicated_line",  # leased line / SLA
]

ALL_NEEDS: tuple[str, ...] = Need.__args__  # type: ignore[attr-defined]


class BusinessProfile(BaseModel):
    business_type: Optional[str] = None
    segment: Optional[Literal["micro", "prof", "multi", "mfg"]] = None
    city: Optional[str] = None
    city_tier: Optional[int] = Field(default=None, ge=1, le=3)
    state: Optional[str] = None
    employees: Optional[int] = Field(default=None, ge=1)
    sites: Optional[int] = Field(default=None, ge=1)
    has_gstin: Optional[bool] = None
    gstin: Optional[str] = None
    gstin_status: Optional[str] = None  # filled by registry lookup
    has_udyam: Optional[bool] = None
    current_internet: Optional[str] = None
    current_provider: Optional[str] = None
    monthly_spend: Optional[int] = Field(default=None, ge=0)
    needs: list[Need] = Field(default_factory=list)
    mobile_lines: Optional[int] = Field(default=None, ge=0)
    cameras: Optional[int] = Field(default=None, ge=0)
    devices: Optional[int] = Field(default=None, ge=0)
    vehicles: Optional[int] = Field(default=None, ge=0)
    machines: Optional[int] = Field(default=None, ge=0)
    fibre_available: Optional[bool] = None
    only_mobile: bool = False
    budget: Optional[int] = Field(default=None, ge=0)

    @property
    def gst_ok(self) -> bool:
        """A product with requires_gstin=Y needs a valid, *active* GSTIN."""
        if not self.has_gstin:
            return False
        return self.gstin_status in (None, "Active")

    def missing_core(self) -> list[str]:
        """Fields the engine cannot recommend without."""
        order = ["business_type", "city", "employees", "sites", "has_gstin", "needs"]
        missing = []
        for f in order:
            v = getattr(self, f)
            if v is None or (f == "needs" and not v and not self.only_mobile):
                missing.append(f)
        return missing
