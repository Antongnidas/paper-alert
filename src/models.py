from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Paper:
    source: str
    category: str
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: Optional[str] = None
    pub_date: Optional[datetime] = None
    link: str = ""
    doi: Optional[str] = None
    matched_keywords: List[str] = field(default_factory=list)
    retrieved_at: Optional[datetime] = None
    raw_date_text: Optional[str] = None