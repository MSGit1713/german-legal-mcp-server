#!/usr/bin/env python3
"""
🧪 UTILS TESTS
==============

Tests für Utility-Funktionen
"""

import pytest
from german_legal_mcp.utils import (
    HTMLProcessor, FTSQueryBuilder, DateParser, 
    TextProcessor, ValidationHelper
)


class TestHTMLProcessor:
    """Tests für HTML-Verarbeitung"""
    
    def test_clean_html_content(self):
        """Test HTML-Bereinigung"""
        html = '<h2>Titel</h2><p>Text mit <strong>Hervorhebung</strong></p>'
        clean = HTMLProcessor.clean_html_content(html)
        
        assert '<' not in clean
        assert '>' not in clean
        assert 'Titel' in clean
        assert 'Text mit Hervorhebung' in clean
    
    def test_clean_empty_html(self):
        """Test leerer HTML-Input"""
        assert HTMLProcessor.clean_html_content("") == ""
        assert HTMLProcessor.clean_html_content(None) == ""
    
    def test_extract_leitsatz_with_tenor(self):
        """Test Leitsatz-Extraktion mit Tenor"""
        html = '<h2>Tenor</h2><p>Die Revision wird zurückgewiesen.</p>'
        leitsatz = HTMLProcessor.extract_leitsatz(html)
        
        assert 'Die Revision wird zurückgewiesen' in leitsatz
    
    def test_extract_leitsatz_with_leitsatz_header(self):
        """Test Leitsatz-Extraktion mit Leitsatz-Header"""
        html = '<h2>Leitsatz</h2><p>Ein wichtiger Rechtsgrundsatz.</p>'
        leitsatz = HTMLProcessor.extract_leitsatz(html)
        
        assert 'Ein wichtiger Rechtsgrundsatz' in leitsatz
    
    def test_extract_leitsatz_max_length(self):
        """Test Leitsatz-Extraktion mit Längenbegrenzung"""
        long_text = "A" * 300
        html = f'<h2>Tenor</h2><p>{long_text}</p>'
        leitsatz = HTMLProcessor.extract_leitsatz(html, max_length=50)
        
        assert len(leitsatz) <= 53  # 50 + "..."
        assert leitsatz.endswith("...")


class TestFTSQueryBuilder:
    """Tests für FTS-Query-Builder"""
    
    def test_build_simple_query(self):
        """Test einfache Query"""
        query = FTSQueryBuilder.build_fts_query("Mietrecht")
        
        assert '"Mietrecht"' in query
        assert 'Mietrecht*' in query
        assert 'OR' in query
    
    def test_build_phrase_query(self):
        """Test Phrasen-Query"""
        query = FTSQueryBuilder.build_fts_query('"fristlose Kündigung"')
        
        assert '"fristlose Kündigung"' in query
    
    def test_build_complex_query(self):
        """Test komplexe Query"""
        query = FTSQueryBuilder.build_fts_query('Arbeitsrecht "fristlose Kündigung"')
        
        assert '"fristlose Kündigung"' in query
        assert '"Arbeitsrecht"' in query
        assert 'Arbeitsrecht*' in query
    
    def test_extract_search_terms(self):
        """Test Suchbegriff-Extraktion"""
        terms = FTSQueryBuilder.extract_search_terms('Mietrecht "fristlose Kündigung" BGH')
        
        assert 'Mietrecht' in terms
        assert 'fristlose Kündigung' in terms
        assert 'BGH' in terms
    
    def test_empty_query(self):
        """Test leere Query"""
        query = FTSQueryBuilder.build_fts_query("")
        assert query == "*"


class TestDateParser:
    """Tests für Datum-Parsing"""
    
    def test_parse_iso_date(self):
        """Test ISO-Datum"""
        date_str, year = DateParser.parse_date("2022-03-15")
        
        assert date_str == "2022-03-15"
        assert year == 2022
    
    def test_parse_german_date(self):
        """Test deutsches Datum"""
        date_str, year = DateParser.parse_date("15.03.2022")
        
        assert date_str == "2022-03-15"
        assert year == 2022
    
    def test_parse_year_only(self):
        """Test nur Jahr"""
        date_str, year = DateParser.parse_date("2022")
        
        assert date_str == "2022-01-01"
        assert year == 2022
    
    def test_parse_invalid_date(self):
        """Test ungültiges Datum"""
        date_str, year = DateParser.parse_date("invalid")
        
        assert date_str is None
        assert year is None
    
    def test_parse_invalid_year(self):
        """Test ungültiges Jahr"""
        date_str, year = DateParser.parse_date("1800-01-01")
        
        assert date_str is None
        assert year is None


class TestTextProcessor:
    """Tests für Text-Verarbeitung"""
    
    def test_clean_text(self):
        """Test Text-Bereinigung"""
        text = "Text  mit   vielen    Leerzeichen"
        clean = TextProcessor.clean_text(text)
        
        assert clean == "Text mit vielen Leerzeichen"
    
    def test_extract_citations(self):
        """Test Zitate-Extraktion"""
        text = "Gemäß § 543 BGB und Art. 14 GG ist die Kündigung zulässig."
        citations = TextProcessor.extract_citations(text)
        
        assert "§ 543" in str(citations)
        assert "Art. 14" in str(citations)
    
    def test_highlight_terms(self):
        """Test Begriff-Hervorhebung"""
        text = "Dies ist ein Test mit wichtigen Begriffen."
        highlighted = TextProcessor.highlight_terms(text, ["Test", "wichtigen"])
        
        assert "<mark>Test</mark>" in highlighted
        assert "<mark>wichtigen</mark>" in highlighted


class TestValidationHelper:
    """Tests für Validierung"""
    
    def test_validate_year_valid(self):
        """Test gültige Jahresangabe"""
        assert ValidationHelper.validate_year(2022) == 2022
        assert ValidationHelper.validate_year("2022") == 2022
    
    def test_validate_year_invalid(self):
        """Test ungültige Jahresangabe"""
        assert ValidationHelper.validate_year(1800) is None
        assert ValidationHelper.validate_year(3000) is None
        assert ValidationHelper.validate_year("invalid") is None
        assert ValidationHelper.validate_year(None) is None
    
    def test_validate_limit(self):
        """Test Limit-Validierung"""
        assert ValidationHelper.validate_limit(10) == 10
        assert ValidationHelper.validate_limit(-5) == 1  # Minimum
        assert ValidationHelper.validate_limit(200) == 100  # Maximum
        assert ValidationHelper.validate_limit("invalid") == 20  # Default
    
    def test_sanitize_search_term(self):
        """Test Suchbegriff-Bereinigung"""
        dangerous = "test<script>alert('xss')</script>"
        clean = ValidationHelper.sanitize_search_term(dangerous)
        
        assert "<script>" not in clean
        assert "alert" not in clean
        assert "test" in clean
