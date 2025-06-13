#!/usr/bin/env python3
"""
📊 DATA MODELS
==============

Typisierte Datenmodelle für German Legal MCP Server
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class Rechtsgebiet(Enum):
    """Rechtsgebiete"""
    ZIVILRECHT = "Zivilrecht"
    ARBEITSRECHT = "Arbeitsrecht"
    SOZIALRECHT = "Sozialrecht"
    VERWALTUNGSRECHT = "Verwaltungsrecht"
    STEUERRECHT = "Steuerrecht"
    VERFASSUNGSRECHT = "Verfassungsrecht"
    STRAFRECHT = "Strafrecht"
    OEFFENTLICHES_RECHT = "Öffentliches Recht"


class Gerichtstyp(Enum):
    """Gerichtstypen"""
    AMTSGERICHT = "Amtsgericht"
    LANDGERICHT = "Landgericht"
    OBERLANDESGERICHT = "Oberlandesgericht"
    BUNDESGERICHTSHOF = "Bundesgerichtshof"
    ARBEITSGERICHT = "Arbeitsgericht"
    LANDESARBEITSGERICHT = "Landesarbeitsgericht"
    BUNDESARBEITSGERICHT = "Bundesarbeitsgericht"
    SOZIALGERICHT = "Sozialgericht"
    LANDESSOZIALGERICHT = "Landessozialgericht"
    BUNDESSOZIALGERICHT = "Bundessozialgericht"
    VERWALTUNGSGERICHT = "Verwaltungsgericht"
    OBERVERWALTUNGSGERICHT = "Oberverwaltungsgericht"
    BUNDESVERWALTUNGSGERICHT = "Bundesverwaltungsgericht"
    FINANZGERICHT = "Finanzgericht"
    BUNDESFINANZHOF = "Bundesfinanzhof"
    VERFASSUNGSGERICHTSHOF = "Verfassungsgerichtshof"
    BUNDESVERFASSUNGSGERICHT = "Bundesverfassungsgericht"


@dataclass
class LegalCase:
    """Rechtsprechungsfall"""
    id: int
    slug: str
    court_name: str
    court_slug: Optional[str] = None
    jurisdiction: Optional[str] = None
    rechtsgebiet: Optional[str] = None
    level_of_appeal: Optional[str] = None
    file_number: Optional[str] = None
    date: Optional[str] = None
    type: Optional[str] = None
    ecli: Optional[str] = None
    content_raw: Optional[str] = None
    content_clean: Optional[str] = None
    content_length: Optional[int] = None
    year: Optional[int] = None
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    indexed_at: Optional[datetime] = None
    
    # Computed fields
    leitsatz: Optional[str] = field(default=None, init=False)
    volltext_url: str = field(default="", init=False)
    
    def __post_init__(self):
        """Post-processing nach Initialisierung"""
        if self.slug:
            self.volltext_url = f"https://de.openlegaldata.io/case/{self.slug}/"
    
    @classmethod
    def from_db_row(cls, row: Any) -> 'LegalCase':
        """Erstellt LegalCase aus Datenbankzeile"""
        return cls(
            id=row[0] if row[0] is not None else 0,
            slug=row[1] or "",
            court_name=row[2] or "",
            court_slug=row[3],
            jurisdiction=row[4],
            rechtsgebiet=row[5],
            level_of_appeal=row[6],
            file_number=row[7],
            date=row[8],
            type=row[9],
            ecli=row[10],
            content_raw=row[11],
            content_clean=row[12],
            content_length=row[13],
            year=row[14],
            created_date=row[15],
            updated_date=row[16]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'id': self.id,
            'slug': self.slug,
            'gericht': self.court_name,
            'rechtsgebiet': self.rechtsgebiet,
            'instanz': self.level_of_appeal,
            'aktenzeichen': self.file_number,
            'datum': self.date,
            'typ': self.type,
            'ecli': self.ecli,
            'jahr': self.year,
            'volltext_url': self.volltext_url,
            'leitsatz': self.leitsatz
        }


@dataclass
class SearchResult:
    """Suchergebnis mit Relevanz-Scoring"""
    case: LegalCase
    relevance_score: float
    snippet: str
    highlighted_terms: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für MCP Response"""
        result = self.case.to_dict()
        result.update({
            'relevanz_score': round(self.relevance_score, 2),
            'snippet': self.snippet,
            'highlighted_terms': self.highlighted_terms
        })
        return result


@dataclass
class SearchQuery:
    """Such-Anfrage"""
    query: str
    rechtsgebiet: Optional[str] = None
    gericht: Optional[str] = None
    jahr_von: Optional[int] = None
    jahr_bis: Optional[int] = None
    limit: int = 20
    
    def validate(self) -> List[str]:
        """Validiert die Suchanfrage"""
        errors = []
        
        if not self.query or not self.query.strip():
            errors.append("Suchbegriff darf nicht leer sein")
        
        if self.limit < 1:
            errors.append("Limit muss mindestens 1 sein")
        elif self.limit > 100:
            errors.append("Limit darf maximal 100 sein")
        
        if self.jahr_von and (self.jahr_von < 1900 or self.jahr_von > 2030):
            errors.append("Startjahr muss zwischen 1900 und 2030 liegen")
        
        if self.jahr_bis and (self.jahr_bis < 1900 or self.jahr_bis > 2030):
            errors.append("Endjahr muss zwischen 1900 und 2030 liegen")
        
        if self.jahr_von and self.jahr_bis and self.jahr_von > self.jahr_bis:
            errors.append("Startjahr darf nicht nach Endjahr liegen")
        
        return errors
    
    def to_cache_key(self) -> str:
        """Erstellt Cache-Key für die Anfrage"""
        return f"{self.query}_{self.rechtsgebiet}_{self.gericht}_{self.jahr_von}_{self.jahr_bis}_{self.limit}"


@dataclass 
class DatabaseStats:
    """Datenbank-Statistiken"""
    total_cases: int
    rechtsgebiete: Dict[str, int] = field(default_factory=dict)
    top_courts: Dict[str, int] = field(default_factory=dict)
    years: Dict[int, int] = field(default_factory=dict)
    content_stats: Optional[Dict[str, float]] = None
    data_quality: Optional[Dict[str, str]] = None
    cache_stats: Optional[Dict[str, Union[int, float]]] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'total_faelle': self.total_cases,
            'rechtsgebiete': self.rechtsgebiete,
            'top_gerichte': self.top_courts,
            'jahre': self.years,
            'content_statistik': self.content_stats,
            'datenqualitaet': self.data_quality,
            'cache_statistik': self.cache_stats,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class Court:
    """Gericht"""
    id: int
    name: str
    court_type: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    code: Optional[str] = None
    jurisdiction: Optional[str] = None
    level_of_appeal: Optional[str] = None
    homepage: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    
    @classmethod
    def from_db_row(cls, row: Any) -> 'Court':
        """Erstellt Court aus Datenbankzeile"""
        return cls(
            id=row[0],
            name=row[1] or "",
            court_type=row[2],
            city=row[3],
            state=row[4],
            code=row[5],
            jurisdiction=row[6],
            level_of_appeal=row[7],
            homepage=row[8],
            address=row[9],
            phone=row[10]
        )


@dataclass
class LawBook:
    """Gesetzbuch"""
    id: int
    code: str
    title: str
    slug: Optional[str] = None
    revision_date: Optional[str] = None
    latest: bool = True
    
    @classmethod
    def from_db_row(cls, row: Any) -> 'LawBook':
        """Erstellt LawBook aus Datenbankzeile"""
        return cls(
            id=row[0],
            code=row[1] or "",
            title=row[2] or "",
            slug=row[3],
            revision_date=row[4],
            latest=bool(row[5]) if row[5] is not None else True
        )


@dataclass
class Law:
    """Einzelnes Gesetz/Paragraph"""
    id: int
    book_id: int
    title: str
    content: Optional[str] = None
    section: Optional[str] = None
    order_num: Optional[int] = None
    book_code: Optional[str] = None
    book_title: Optional[str] = None
    
    @classmethod
    def from_db_row(cls, row: Any) -> 'Law':
        """Erstellt Law aus Datenbankzeile"""
        return cls(
            id=row[0],
            book_id=row[1],
            title=row[2] or "",
            content=row[3],
            section=row[4],
            order_num=row[5],
            book_code=row[6],
            book_title=row[7]
        )


# Type Aliases für bessere Lesbarkeit
CaseList = List[LegalCase]
SearchResults = List[SearchResult]
CourtList = List[Court]
LawList = List[Law]
