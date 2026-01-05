#!/usr/bin/env python3
"""
GR International YouTube Channel Analyzer
Extrait et analyse toutes les vidéos de la chaîne YouTube GR International.

Usage:
    python execution/gr_youtube_analyzer.py                    # Extraction complète
    python execution/gr_youtube_analyzer.py --max 10           # Limiter à 10 vidéos
    python execution/gr_youtube_analyzer.py --transcripts      # Inclure les transcriptions
    python execution/gr_youtube_analyzer.py --visible          # Mode debug (affiche le navigateur)
"""

import json
import argparse
import re
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import subprocess
import sys

# Chemins
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / ".tmp"
OUTPUT_JSON = OUTPUT_DIR / "gr_youtube_videos.json"
OUTPUT_MD = OUTPUT_DIR / "gr_youtube_analysis.md"

# Configuration
CHANNEL_URL = "https://www.youtube.com/@grinternational"
CHANNEL_VIDEOS_URL = f"{CHANNEL_URL}/videos"


@dataclass
class YouTubeVideo:
    """Structure d'une vidéo YouTube"""
    video_id: str
    title: str
    url: str
    upload_date: Optional[str] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    transcript: Optional[str] = None
    transcript_language: Optional[str] = None


def install_dependencies():
    """Installe les dépendances nécessaires"""
    dependencies = ["yt-dlp", "youtube-transcript-api"]
    for dep in dependencies:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            print(f"Installation de {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "-q"])


def get_channel_videos(channel_url: str, max_videos: int = None) -> list[dict]:
    """Récupère la liste des vidéos d'une chaîne YouTube via yt-dlp"""
    import yt_dlp

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'force_generic_extractor': False,
    }

    if max_videos:
        ydl_opts['playlistend'] = max_videos

    videos = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Récupérer la page des vidéos de la chaîne
            result = ydl.extract_info(f"{channel_url}/videos", download=False)

            if result and 'entries' in result:
                for entry in result['entries']:
                    if entry:
                        videos.append({
                            'video_id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
                            'duration': entry.get('duration'),
                            'view_count': entry.get('view_count'),
                        })
        except Exception as e:
            print(f"Erreur lors de la récupération des vidéos: {e}")

    return videos


def get_video_details(video_id: str) -> dict:
    """Récupère les détails complets d'une vidéo"""
    import yt_dlp

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return {
                'video_id': video_id,
                'title': result.get('title'),
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'upload_date': result.get('upload_date'),
                'duration': result.get('duration_string'),
                'duration_seconds': result.get('duration'),
                'view_count': result.get('view_count'),
                'like_count': result.get('like_count'),
                'description': result.get('description'),
                'thumbnail_url': result.get('thumbnail'),
            }
        except Exception as e:
            print(f"Erreur pour la vidéo {video_id}: {e}")
            return None


def get_video_transcript(video_id: str) -> tuple[str, str]:
    """Récupère la transcription d'une vidéo YouTube"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # Essayer d'abord en français, puis en anglais, puis n'importe quelle langue
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Priorité: français > anglais > autre
        transcript = None
        language = None

        try:
            transcript = transcript_list.find_transcript(['fr', 'fr-CA'])
            language = 'fr'
        except:
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
                language = 'en'
            except:
                try:
                    # Prendre la première disponible
                    for t in transcript_list:
                        transcript = t
                        language = t.language_code
                        break
                except:
                    pass

        if transcript:
            text_parts = [entry['text'] for entry in transcript.fetch()]
            return ' '.join(text_parts), language

    except Exception as e:
        # Pas de transcription disponible
        pass

    return None, None


def format_duration(seconds: int) -> str:
    """Formate une durée en secondes en format lisible"""
    if not seconds:
        return "N/A"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{secs:02d}s"
    return f"{minutes}m{secs:02d}s"


def format_date(date_str: str) -> str:
    """Formate une date YYYYMMDD en format lisible"""
    if not date_str or len(date_str) != 8:
        return "N/A"
    try:
        date = datetime.strptime(date_str, "%Y%m%d")
        return date.strftime("%Y-%m-%d")
    except:
        return date_str


def format_number(num: int) -> str:
    """Formate un nombre avec séparateurs"""
    if num is None:
        return "N/A"
    return f"{num:,}".replace(",", " ")


def analyze_channel(max_videos: int = None, include_transcripts: bool = False, verbose: bool = False) -> dict:
    """Analyse complète de la chaîne YouTube"""

    print(f"\n{'='*60}")
    print("GR International - Analyse YouTube")
    print(f"{'='*60}\n")

    # Étape 1: Récupérer la liste des vidéos
    print("[VIDEO] Recuperation de la liste des videos...")
    videos_basic = get_channel_videos(CHANNEL_URL, max_videos)
    print(f"   -> {len(videos_basic)} videos trouvees")

    if not videos_basic:
        print("[ERREUR] Aucune video trouvee")
        return None

    # Étape 2: Récupérer les détails de chaque vidéo
    videos = []
    print("\n[STATS] Recuperation des details...")

    for i, v in enumerate(videos_basic, 1):
        video_id = v.get('video_id')
        if not video_id:
            continue

        title_display = v.get('title', 'Sans titre')[:50].encode('ascii', 'replace').decode('ascii')
        print(f"   [{i}/{len(videos_basic)}] {title_display}...")

        details = get_video_details(video_id)
        if details:
            video = YouTubeVideo(**details)

            # Transcription si demandée
            if include_transcripts:
                print(f"      -> Recuperation transcription...")
                transcript, lang = get_video_transcript(video_id)
                video.transcript = transcript
                video.transcript_language = lang
                if transcript:
                    print(f"      -> Transcription ({lang}): {len(transcript)} caracteres")

            videos.append(video)

    # Étape 3: Calculer les statistiques
    total_views = sum(v.view_count or 0 for v in videos)
    total_duration = sum(v.duration_seconds or 0 for v in videos)
    total_likes = sum(v.like_count or 0 for v in videos)

    # Trier par date
    videos_sorted = sorted(videos, key=lambda x: x.upload_date or "", reverse=True)

    # Trier par vues
    videos_by_views = sorted(videos, key=lambda x: x.view_count or 0, reverse=True)

    result = {
        "channel": "GR International",
        "channel_url": CHANNEL_URL,
        "extraction_date": datetime.now().isoformat(),
        "total_videos": len(videos),
        "total_views": total_views,
        "total_duration_seconds": total_duration,
        "total_duration_formatted": format_duration(total_duration),
        "total_likes": total_likes,
        "average_views": total_views // len(videos) if videos else 0,
        "videos": [asdict(v) for v in videos_sorted],
        "top_videos_by_views": [asdict(v) for v in videos_by_views[:10]],
    }

    return result


def generate_markdown_report(data: dict) -> str:
    """Génère un rapport Markdown à partir des données"""

    lines = [
        "# Analyse YouTube - GR International",
        "",
        f"**Chaîne**: [{data['channel']}]({data['channel_url']})",
        f"**Date d'extraction**: {data['extraction_date'][:10]}",
        "",
        "---",
        "",
        "## Résumé",
        "",
        "| Métrique | Valeur |",
        "|----------|--------|",
        f"| Nombre de vidéos | {data['total_videos']} |",
        f"| Vues totales | {format_number(data['total_views'])} |",
        f"| Durée totale | {data['total_duration_formatted']} |",
        f"| Likes totaux | {format_number(data['total_likes'])} |",
        f"| Moyenne de vues | {format_number(data['average_views'])} |",
        "",
        "---",
        "",
        "## Top 10 Vidéos (par vues)",
        "",
        "| # | Titre | Vues | Durée | Date |",
        "|---|-------|------|-------|------|",
    ]

    for i, video in enumerate(data.get('top_videos_by_views', [])[:10], 1):
        title = video.get('title', 'Sans titre')[:50]
        if len(video.get('title', '')) > 50:
            title += "..."
        views = format_number(video.get('view_count'))
        duration = video.get('duration') or format_duration(video.get('duration_seconds'))
        date = format_date(video.get('upload_date'))
        url = video.get('url', '')
        lines.append(f"| {i} | [{title}]({url}) | {views} | {duration} | {date} |")

    lines.extend([
        "",
        "---",
        "",
        "## Toutes les Vidéos (par date)",
        "",
        "| Date | Titre | Vues | Durée |",
        "|------|-------|------|-------|",
    ])

    for video in data.get('videos', []):
        title = video.get('title', 'Sans titre')[:60]
        if len(video.get('title', '')) > 60:
            title += "..."
        views = format_number(video.get('view_count'))
        duration = video.get('duration') or format_duration(video.get('duration_seconds'))
        date = format_date(video.get('upload_date'))
        url = video.get('url', '')
        lines.append(f"| {date} | [{title}]({url}) | {views} | {duration} |")

    # Analyse des transcriptions si disponibles
    videos_with_transcripts = [v for v in data.get('videos', []) if v.get('transcript')]
    if videos_with_transcripts:
        lines.extend([
            "",
            "---",
            "",
            "## Transcriptions Disponibles",
            "",
            f"**{len(videos_with_transcripts)} vidéos avec transcription**",
            "",
        ])

        for video in videos_with_transcripts[:5]:  # Limiter aux 5 premières
            lines.extend([
                f"### {video.get('title', 'Sans titre')}",
                "",
                f"**Langue**: {video.get('transcript_language', 'N/A')}",
                f"**Longueur**: {len(video.get('transcript', ''))} caractères",
                "",
                "**Extrait**:",
                f"> {video.get('transcript', '')[:500]}...",
                "",
            ])

    lines.extend([
        "",
        "---",
        "",
        "*Rapport généré automatiquement par gr_youtube_analyzer.py*",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyse la chaîne YouTube GR International")
    parser.add_argument("--max", type=int, help="Nombre maximum de vidéos à analyser")
    parser.add_argument("--transcripts", action="store_true", help="Inclure les transcriptions")
    parser.add_argument("--visible", action="store_true", help="Mode verbose")
    args = parser.parse_args()

    # Installer les dépendances si nécessaire
    install_dependencies()

    # Créer le dossier de sortie
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Analyser la chaîne
    data = analyze_channel(
        max_videos=args.max,
        include_transcripts=args.transcripts,
        verbose=args.visible
    )

    if not data:
        print("\n[ERREUR] Echec de l'analyse")
        return 1

    # Sauvegarder le JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] JSON sauvegarde: {OUTPUT_JSON}")

    # Générer le rapport Markdown
    report = generate_markdown_report(data)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[OK] Rapport sauvegarde: {OUTPUT_MD}")

    # Afficher le résumé
    print(f"\n{'='*60}")
    print("RESUME")
    print(f"{'='*60}")
    print(f"[VIDEO] Videos analysees: {data['total_videos']}")
    print(f"[VUES] Vues totales: {format_number(data['total_views'])}")
    print(f"[DUREE] Duree totale: {data['total_duration_formatted']}")
    print(f"[LIKES] Likes totaux: {format_number(data['total_likes'])}")

    if data.get('top_videos_by_views'):
        print(f"\n[TOP] Top video: {data['top_videos_by_views'][0].get('title', 'N/A')}")
        print(f"   -> {format_number(data['top_videos_by_views'][0].get('view_count'))} vues")

    return 0


if __name__ == "__main__":
    exit(main())
