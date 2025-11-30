from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DomainInfo(BaseModel):
    is_registered: bool = Field(..., description="Domain registration status.")
    owner_simulated: Optional[str] = None
    expiration_date: Optional[str] = None

class SocialMediaHits(BaseModel):
    platform: str
    url_found: Optional[str] = None
    status: str

class VulnerabilityHit(BaseModel):
    source: str
    cve_id: Optional[str] = None
    severity: str
    description: str

class WebSearchHit(BaseModel):
    source: str
    result_type: str
    data: Any 

class DigitalFootprintReport(BaseModel):
    target: str = Field(..., description="The entity (domain/username) analyzed.")
    timestamp: str
    summary: str
    is_cached: bool = False
    
    domain_results: Optional[DomainInfo] = None
    social_media_hits: List[SocialMediaHits] = Field(default_factory=list)
    vulnerability_hits: List[VulnerabilityHit] = Field(default_factory=list)
    web_search_data: List[WebSearchHit] = Field(default_factory=list)