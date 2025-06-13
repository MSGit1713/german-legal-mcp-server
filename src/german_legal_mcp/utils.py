#!/usr/bin/env python3
"""
🛠️ UTILITIES
=============

Hilfsfunktionen für German Legal MCP Server
"""

import re
import html
import logging
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)


class HTMLProcessor:
    """HTML-Verarbeitung für Rechtsdokumente"""
    
    @staticmethod
    def clean_html_content(html_content: str) -> str:
        """Bereinigt HTML-Content für FTS"""
        if not html_content:
            return ""
        
        # HTML-Tags entfernen
        clean_text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # HTML-Entities dekodieren
        clean_text = html.unescape(clean_text)
        
        # Spezielle Zeichen normalisieren
        clean_text = re.sub(r'&nbsp;', ' ', clean_text)
        clean_text = re.sub(r'&[a-zA-Z]+;', ' ', clean_text)
        
        # Mehrfache Leerzeichen normalisieren
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Trim
        clean_text = clean_text.strip()
        
        return clean_text
    
    @staticmethod
    def extract_leitsatz(content: str, max_length: int = 200) -> str:
        """Extrahiert Leitsatz aus Urteilstext"""
        if not content:
            return ""
        
        # Erweiterte Patterns für Leitsatz-Extraktion
        patterns = [
            # HTML-Strukturen
            r'<h2[^>]*>Tenor</h2>\s*<[^>]*>\s*([^<]+)',
            r'<h2[^>]*>Leitsatz</h2>\s*<[^>]*>\s*([^<]+)',
            r'<h3[^>]*>Tenor</h3>\s*<[^>]*>\s*([^<]+)',
            r'<h3[^>]*>Leitsätze?</h3>\s*<[^>]*>\s*([^<]+)',
            
            # Text-Strukturen
            r'(?i)tenor[:\s]*([^<\n]+)',
            r'(?i)leitsatz[:\s]*([^<\n]+)',
            r'(?i)leitsätze[:\s]*([^<\n]+)',
            
            # Nummerierte Strukturen
            r'(?:^|\n)(\d+\.\s+[^<\n]+)',
            r'(?:^|\n)(I\.\s+[^<\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                leitsatz = html.unescape(match.group(1).strip())
                leitsatz = re.sub(r'\s+', ' ', leitsatz)
                
                if len(leitsatz) > max_length:
                    leitsatz = leitsatz[:max_length] + "..."
                
                return leitsatz
        
        # Fallback: Erste Sätze des bereinigten Texts
        clean_content = HTMLProcessor.clean_html_content(content)
        if clean_content:
            sentences = re.split(r'[.!?]+', clean_content)
            if sentences and sentences[0].strip():
                first_sentence = sentences[0].strip()
                if len(first_sentence) > max_length:
                    first_sentence = first_sentence[:max_length] + "..."
                return first_sentence
        
        return ""


class FTSQueryBuilder:
    """FTS5-Query-Builder für erweiterte Suche"""
    
    @staticmethod
    def build_fts_query(query: str) -> str:
        """Erstellt optimierte FTS5-Query"""
        if not query:
            return "*"
        
        # Phrasen in Anführungszeichen erkennen
        phrases = re.findall(r'"([^"]*)"', query)
        remaining = re.sub(r'"[^"]*"', '', query)
        
        terms = []
        
        # Phrasen als exakte Suche
        for phrase in phrases:
            if phrase.strip():
                terms.append(f'"{phrase.strip()}"')
        
        # Einzelne Begriffe mit Varianten
        for term in remaining.split():
            if len(term) > 2:
                # Exakte Suche
                terms.append(f'"{term}"')
                # Präfix-Suche für Wortformen
                terms.append(f'{term}*')
        
        if not terms:
            return f'"{query}"'
        
        return " OR ".join(terms)
    
    @staticmethod
    def extract_search_terms(query: str) -> List[str]:
        """Extrahiert Suchbegriffe für Highlighting"""
        terms = []
        
        # Phrasen
        phrases = re.findall(r'"([^"]*)"', query)
        terms.extend([phrase.strip() for phrase in phrases if phrase.strip()])
        
        # Einzelne Begriffe
        remaining = re.sub(r'"[^"]*"', '', query)
        words = [word.strip() for word in remaining.split() if len(word.strip()) > 2]
        terms.extend(words)
        
        return list(set(terms))  # Duplikate entfernen


class DateParser:
    """Datum-Parsing für deutsche Rechtsdokumente"""
    
    @staticmethod
    def parse_date(date_str: str) -> Tuple[Optional[str], Optional[int]]:
        """Parst Datum und extrahiert Jahr"""
        if not date_str:
            return None, None
        
        # Standard ISO-Format
        iso_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', date_str)
        if iso_match:
            year = int(iso_match.group(1))
            if 1900 <= year <= 2030:
                return date_str, year
        
        # Deutsches Format
        de_match = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', date_str)
        if de_match:
            day, month, year = de_match.groups()
            year = int(year)
            if 1900 <= year <= 2030:
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}", year
        
        # Nur Jahr
        year_match = re.match(r'(\d{4})', date_str)
        if year_match:
            year = int(year_match.group(1))
            if 1900 <= year <= 2030:
                return f"{year}-01-01", year
        
        return None, None


class FileManager:
    """File-Management Utilities"""
    
    @staticmethod
    def find_database_files(search_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """Findet Datenbankdateien in den angegebenen Pfaden"""
        found_files = {}
        
        for path_str in search_paths:
            try:
                path = Path(path_str)
                if path.exists() and path.is_file():
                    stat = path.stat()
                    found_files[str(path)] = {
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'readable': path.is_file() and path.stat().st_size > 0
                    }
            except Exception as e:
                logger.debug(f"Fehler beim Prüfen von {path_str}: {e}")
        
        return found_files
    
    @staticmethod
    def get_file_hash(file_path: str) -> Optional[str]:
        """Erstellt Hash für Datei"""
        try:
            with open(file_path, 'rb') as f:
                # Nur ersten 1MB für Hash verwenden (Performance)
                content = f.read(1024 * 1024)
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.debug(f"Fehler beim Hash-Erstellen für {file_path}: {e}")
            return None


class TextProcessor:
    """Text-Verarbeitung für Rechtsdokumente"""
    
    @staticmethod
    @staticmethod
    def clean_text(text: str) -> str:
        """Bereinigt Text für bessere Verarbeitung"""
        if not text:
            return ""
        
        # Mehrfache Leerzeichen normalisieren
        text = re.sub(r'\s+', ' ', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_citations(text: str) -> List[str]:
        """Extrahiert Zitate aus Rechtstext"""
        citations = []
        
        # Paragraphen-Referenzen
        para_refs = re.findall(r'§\s*(\d+[a-z]?)\s*(?:Abs\.\s*\d+\s*)?(?:Satz\s*\d+\s*)?(?:[A-Z]{2,}(?:\s+[A-Z]{2,})*)', text)
        citations.extend([f"§ {ref}" for ref in para_refs])
        
        # Artikel-Referenzen
        art_refs = re.findall(r'Art\.\s*(\d+[a-z]?)\s*(?:Abs\.\s*\d+\s*)?(?:GG|EMRK|EU-Vertrag)', text)
        citations.extend([f"Art. {ref}" for ref in art_refs])
        
        return list(set(citations))  # Duplikate entfernen
    
    @staticmethod
    def highlight_terms(text: str, terms: List[str], max_length: int = 300) -> str:
        """Markiert Suchbegriffe im Text"""
        if not text or not terms:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        highlighted = text
        
        for term in terms:
            if len(term) > 2:  # Nur längere Terme markieren
                pattern = re.escape(term)
                highlighted = re.sub(
                    f'({pattern})', 
                    r'<mark>\1</mark>', 
                    highlighted, 
                    flags=re.IGNORECASE
                )
        
        # Kürzen falls nötig
        if len(highlighted) > max_length:
            highlighted = highlighted[:max_length] + "..."
        
        return highlighted


class ValidationHelper:
    """Validierungs-Hilfsfunktionen"""
    
    @staticmethod
    def validate_year(year: Any) -> Optional[int]:
        """Validiert Jahresangabe"""
        if year is None:
            return None
        
        try:
            year_int = int(year)
            if 1900 <= year_int <= 2030:
                return year_int
        except (ValueError, TypeError):
            pass
        
        return None
    
    @staticmethod
    def validate_limit(limit: Any, min_val: int = 1, max_val: int = 100) -> int:
        """Validiert Limit-Parameter"""
        try:
            limit_int = int(limit)
            return max(min_val, min(limit_int, max_val))
        except (ValueError, TypeError):
            return 20  # Default
    
    @staticmethod
    def sanitize_search_term(term: str) -> str:
        """Bereinigt Suchbegriff"""
        if not term:
            return ""
        
        # Gefährliche Zeichen entfernen
        term = re.sub(r'[<>;&|`$(){}[\]\\]', '', term)
        
        # Mehrfache Leerzeichen normalisieren
        term = re.sub(r'\s+', ' ', term)
        
        # Trim
        term = term.strip()
        
        return term


class PerformanceHelper:
    """Performance-Hilfsfunktionen"""
    
    @staticmethod
    def measure_time(func):
        """Decorator für Zeit-Messung"""
        def wrapper(*args, **kwargs):
            start = datetime.now()
            result = func(*args, **kwargs)
            end = datetime.now()
            duration = (end - start).total_seconds()
            logger.debug(f"{func.__name__} took {duration:.3f}s")
            return result
        return wrapper
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Formatiert Dateigröße"""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {units[i]}"
    
    @staticmethod
    def format_number(num: int) -> str:
        """Formatiert Zahlen mit Tausender-Trennzeichen"""
        return f"{num:,}".replace(",", ".")
