#!/usr/bin/env python3
"""
🖥️ MCP SERVER - FORMATTING METHODS
===================================

Formatierungsmethoden für den German Legal MCP Server
"""

from typing import List
from .models import SearchResult, LegalCase, DatabaseStats
from .utils import PerformanceHelper


class GermanLegalMCPServerFormatting:
    """Formatierungsmethoden für MCP Server Responses"""
    
    @staticmethod
    def _format_search_results(results: List[SearchResult], 
                             suchbegriff: str, 
                             advanced: bool = False) -> str:
        """Formatiert Suchergebnisse für Ausgabe"""
        
        title_prefix = "🔍 **Erweiterte" if advanced else "🏛️ **"
        output = f"{title_prefix} Rechtsprechungssuche:** '{suchbegriff}'\n\n"
        output += f"**📊 {len(results)} Ergebnisse gefunden**\n\n"
        
        for i, result in enumerate(results, 1):
            case = result.case
            
            # Header mit Gericht und Aktenzeichen
            output += f"**{i}. {case.court_name}**\n"
            
            # Basis-Informationen
            info_parts = []
            if case.file_number:
                info_parts.append(f"📋 {case.file_number}")
            if case.date:
                info_parts.append(f"📅 {case.date}")
            if case.year:
                info_parts.append(f"({case.year})")
            
            if info_parts:
                output += " | ".join(info_parts) + "\n"
            
            # Rechtsgebiet und Instanz
            meta_parts = []
            if case.rechtsgebiet:
                meta_parts.append(f"🏷️ {case.rechtsgebiet}")
            if case.level_of_appeal:
                meta_parts.append(f"⚖️ {case.level_of_appeal}")
            if case.type:
                meta_parts.append(f"📄 {case.type}")
            
            if meta_parts:
                output += " | ".join(meta_parts) + "\n"
            
            # Relevanz-Score
            output += f"📊 **Relevanz:** {result.relevance_score}\n"
            
            # Leitsatz
            if case.leitsatz:
                output += f"💡 **Leitsatz:** {case.leitsatz}\n"
            
            # Snippet
            if result.snippet and result.snippet.strip():
                output += f"📄 **Auszug:** {result.snippet}\n"
            
            # Links
            output += f"🔗 [Volltext anzeigen]({case.volltext_url})\n"
            if case.ecli:
                output += f"⚖️ **ECLI:** {case.ecli}\n"
            
            # Highlighted Terms (für erweiterte Suche)
            if advanced and result.highlighted_terms:
                terms = ", ".join(result.highlighted_terms[:5])
                output += f"🔍 **Suchbegriffe:** {terms}\n"
            
            output += f"🆔 **Fall-ID:** {case.id}\n"
            output += "\n---\n\n"
        
        # Footer mit Hinweisen
        output += "💡 **Hinweise:**\n"
        output += "- Verwenden Sie die Fall-ID für ähnliche Fälle: `aehnliche_faelle`\n"
        output += "- Für Details zu einem Fall: `fall_details`\n"
        output += "- Erweiterte Filter: `erweiterte_suche`\n"
        
        return output
    
    @staticmethod
    def _format_similar_cases(results: List[SearchResult], reference_id: int) -> str:
        """Formatiert ähnliche Fälle"""
        
        output = f"🔗 **Ähnliche Fälle zu Fall-ID {reference_id}**\n\n"
        output += f"**📊 {len(results)} ähnliche Fälle gefunden**\n\n"
        
        for i, result in enumerate(results, 1):
            case = result.case
            
            output += f"**{i}. {case.court_name}** (ID: {case.id})\n"
            
            # Basis-Info
            if case.file_number:
                output += f"📋 {case.file_number}"
            if case.date:
                output += f" | 📅 {case.date}"
            if case.rechtsgebiet:
                output += f" | 🏷️ {case.rechtsgebiet}"
            output += "\n"
            
            # Ähnlichkeits-Score
            output += f"🎯 **Ähnlichkeit:** {result.relevance_score}\n"
            
            # Kurzer Leitsatz
            if case.leitsatz:
                leitsatz = case.leitsatz[:150] + "..." if len(case.leitsatz) > 150 else case.leitsatz
                output += f"💡 {leitsatz}\n"
            
            output += f"🔗 [Volltext]({case.volltext_url})\n\n"
        
        return output
    
    @staticmethod
    def _format_case_details(case: LegalCase) -> str:
        """Formatiert detaillierte Fall-Informationen"""
        
        output = f"📋 **Detaillierte Fall-Informationen (ID: {case.id})**\n\n"
        
        # Gericht und Verfahren
        output += f"**🏛️ Gericht:** {case.court_name}\n"
        if case.jurisdiction:
            output += f"**⚖️ Gerichtsbarkeit:** {case.jurisdiction}\n"
        if case.level_of_appeal:
            output += f"**🔺 Instanz:** {case.level_of_appeal}\n"
        
        output += "\n**📄 Verfahrensdaten:**\n"
        if case.file_number:
            output += f"- **Aktenzeichen:** {case.file_number}\n"
        if case.date:
            output += f"- **Datum:** {case.date}\n"
        if case.year:
            output += f"- **Jahr:** {case.year}\n"
        if case.type:
            output += f"- **Typ:** {case.type}\n"
        if case.ecli:
            output += f"- **ECLI:** {case.ecli}\n"
        
        # Rechtsgebiet
        if case.rechtsgebiet:
            output += f"\n**🏷️ Rechtsgebiet:** {case.rechtsgebiet}\n"
        
        # Leitsatz
        if case.leitsatz:
            output += f"\n**💡 Leitsatz:**\n{case.leitsatz}\n"
        
        # Content-Informationen
        if case.content_length:
            output += f"\n**📊 Content-Information:**\n"
            output += f"- **Textlänge:** {PerformanceHelper.format_number(case.content_length)} Zeichen\n"
        
        # Metadaten
        output += f"\n**🔗 Links und Referenzen:**\n"
        output += f"- **Volltext:** {case.volltext_url}\n"
        output += f"- **Slug:** {case.slug}\n"
        
        if case.created_date:
            output += f"\n**📅 Erstellt:** {case.created_date}\n"
        if case.updated_date:
            output += f"**📝 Aktualisiert:** {case.updated_date}\n"
        
        # Aktionen
        output += f"\n**💡 Mögliche Aktionen:**\n"
        output += f"- Ähnliche Fälle finden: `aehnliche_faelle` mit Fall-ID {case.id}\n"
        output += f"- Nach Gericht suchen: `suche_rechtsprechung` mit '{case.court_name}'\n"
        if case.rechtsgebiet:
            output += f"- Nach Rechtsgebiet suchen: Filter '{case.rechtsgebiet}'\n"
        
        return output
    
    @staticmethod
    def _format_database_stats(stats: DatabaseStats, 
                             cache_stats: dict, 
                             detailliert: bool = False) -> str:
        """Formatiert Datenbankstatistiken"""
        
        output = "📊 **German Legal Database - Statistik**\n\n"
        
        # Basis-Statistiken
        output += f"**📚 Gesamtübersicht:**\n"
        output += f"- **Gesamte Fälle:** {PerformanceHelper.format_number(stats.total_cases)}\n"
        output += f"- **Letzte Aktualisierung:** {stats.last_updated.strftime('%d.%m.%Y %H:%M')}\n"
        
        # Cache-Performance
        output += f"\n**⚡ Such-Performance:**\n"
        output += f"- **Cache Hit-Rate:** {cache_stats['hit_rate']}%\n"
        output += f"- **Cache-Größe:** {cache_stats['cache_size']}/{cache_stats['max_size']}\n"
        output += f"- **Cache Hits:** {PerformanceHelper.format_number(cache_stats['hits'])}\n"
        output += f"- **Cache Misses:** {PerformanceHelper.format_number(cache_stats['misses'])}\n"
        
        # Rechtsgebiete
        if stats.rechtsgebiete:
            output += f"\n**⚖️ Rechtsgebiete (Top 10):**\n"
            for i, (gebiet, count) in enumerate(list(stats.rechtsgebiete.items())[:10], 1):
                percentage = (count / stats.total_cases) * 100
                output += f"{i}. {gebiet}: {PerformanceHelper.format_number(count)} ({percentage:.1f}%)\n"
        
        # Top Gerichte
        if stats.top_courts:
            output += f"\n**🏛️ Top Gerichte (Top 10):**\n"
            for i, (gericht, count) in enumerate(list(stats.top_courts.items())[:10], 1):
                output += f"{i}. {gericht}: {PerformanceHelper.format_number(count)}\n"
        
        # Jahre
        if stats.years:
            output += f"\n**📅 Aktuelle Jahre (Top 10):**\n"
            for jahr, count in list(stats.years.items())[:10]:
                output += f"- {jahr}: {PerformanceHelper.format_number(count)}\n"
        
        # Detaillierte Statistiken
        if detailliert:
            if stats.content_stats:
                output += f"\n**📄 Content-Statistiken:**\n"
                cs = stats.content_stats
                output += f"- **Durchschnittliche Länge:** {PerformanceHelper.format_number(cs['durchschnittliche_laenge'])} Zeichen\n"
                output += f"- **Min/Max Länge:** {PerformanceHelper.format_number(cs['minimale_laenge'])} / {PerformanceHelper.format_number(cs['maximale_laenge'])}\n"
                output += f"- **Mit substantiellem Inhalt:** {PerformanceHelper.format_number(cs['mit_inhalt'])}\n"
            
            if stats.data_quality:
                output += f"\n**✅ Datenqualität:**\n"
                dq = stats.data_quality
                output += f"- **Mit ECLI:** {dq['mit_ecli']}\n"
                output += f"- **Mit Datum:** {dq['mit_datum']}\n"
                output += f"- **Mit Aktenzeichen:** {dq['mit_aktenzeichen']}\n"
        
        # Nutzungshinweise
        output += f"\n**💡 Nutzungshinweise:**\n"
        output += f"- Verwenden Sie spezifische Rechtsgebiete für bessere Ergebnisse\n"
        output += f"- Kombinieren Sie mehrere Filter für präzise Suchen\n"
        output += f"- Nutzen Sie Anführungszeichen für exakte Phrasen\n"
        output += f"- Der Cache verbessert die Performance bei wiederholten Suchen\n"
        
        return output


# Mixin für den Hauptserver
class ServerFormattingMixin(GermanLegalMCPServerFormatting):
    """Mixin um Formatierungsmethoden in Server-Klasse zu integrieren"""
    pass
