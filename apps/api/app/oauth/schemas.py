from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class OAuthProvider(StrEnum):
    meta = "meta"


class ProviderAccountType(StrEnum):
    instagram_business = "instagram_business"
    facebook_page = "facebook_page"
    whatsapp_business = "whatsapp_business"


@dataclass(frozen=True)
class OAuthAccessToken:
    access_token: str
    expires_at: datetime | None = None
