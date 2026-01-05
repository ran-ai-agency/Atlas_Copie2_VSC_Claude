# Directive: GR International - Analyse YouTube

## Objectif
Extraire et analyser toutes les vidéos de la chaîne YouTube GR International pour:
- Identifier les contenus les plus performants
- Comprendre les tendances de publication
- Exploiter les transcriptions pour l'analyse stratégique
- Suivre l'évolution de la communication de GR International

## Contexte

### Chaîne YouTube GR International
- **URL**: https://www.youtube.com/@grinternational
- **Type de contenus**: Nouvelles hebdomadaires, témoignages, formations, événements
- **Langues**: Français et Anglais (versions séparées des nouvelles)
- **Fréquence**: ~2 vidéos par semaine (nouvelles FR et EN)

### Types de Vidéos Identifiés
1. **Nouvelles hebdomadaires** - "GR Réseautage en affaires, nouvelles du [date]"
2. **Nouvelles anglaises** - "GR Business Networking News [date]"
3. **Témoignages membres** - Présentations de membres et partenaires
4. **Formations** - Ateliers, tutoriels (ChatGPT, intranet, etc.)
5. **Événements** - Conventions, conférences
6. **Promotions** - Black Friday, Boxing Day, offres spéciales

## Inputs
- **Chaîne YouTube**: `https://www.youtube.com/@grinternational`
- **Script d'extraction**: `execution/gr_youtube_analyzer.py`

## Script d'Extraction

### Utilisation

**Extraction complète (toutes les vidéos):**
```bash
python execution/gr_youtube_analyzer.py
```

**Extraction limitée (test avec N vidéos):**
```bash
python execution/gr_youtube_analyzer.py --max 10
```

**Avec transcriptions (plus lent):**
```bash
python execution/gr_youtube_analyzer.py --transcripts
```

**Mode verbose:**
```bash
python execution/gr_youtube_analyzer.py --visible
```

### Dépendances
```bash
pip install yt-dlp youtube-transcript-api
```

## Outputs

### Fichiers Générés
1. **`.tmp/gr_youtube_videos.json`** - Données complètes de toutes les vidéos
2. **`.tmp/gr_youtube_analysis.md`** - Rapport Markdown formaté

### Structure JSON
```json
{
  "channel": "GR International",
  "channel_url": "https://www.youtube.com/@grinternational",
  "extraction_date": "2026-01-04T...",
  "total_videos": 306,
  "total_views": 50000,
  "total_duration_seconds": 36000,
  "total_duration_formatted": "10h00m00s",
  "total_likes": 500,
  "average_views": 163,
  "videos": [
    {
      "video_id": "abc123",
      "title": "GR Réseautage en affaires...",
      "url": "https://www.youtube.com/watch?v=abc123",
      "upload_date": "20251214",
      "duration": "2:15",
      "duration_seconds": 135,
      "view_count": 50,
      "like_count": 2,
      "description": "...",
      "thumbnail_url": "...",
      "transcript": "...",
      "transcript_language": "fr"
    }
  ],
  "top_videos_by_views": [...]
}
```

## Cas d'Usage

### 1. Analyse des Performances
- Identifier les vidéos les plus vues
- Calculer le taux d'engagement (likes/vues)
- Comparer les performances FR vs EN

### 2. Analyse de Contenu
- Extraire les transcriptions des meilleures vidéos
- Identifier les thèmes récurrents
- Analyser les annonces importantes

### 3. Veille Stratégique
- Suivre les nouvelles promotions GR
- Identifier les événements à venir
- Repérer les nouveaux membres/partenaires mentionnés

### 4. Inspiration pour Vaudreuil-Dorion 1
- S'inspirer des formats performants
- Identifier les meilleures pratiques
- Proposer du contenu pour la chaîne

## Métriques Clés

| Métrique | Description |
|----------|-------------|
| Total vidéos | Nombre de vidéos sur la chaîne |
| Vues totales | Cumul des vues de toutes les vidéos |
| Durée totale | Temps total de contenu |
| Moyenne vues | Vues moyennes par vidéo |
| Top 10 | Vidéos les plus performantes |

## Fréquence de Mise à Jour
- **Extraction complète**: Mensuelle
- **Mise à jour incrémentale**: Hebdomadaire (nouvelles vidéos)

## Intégration avec Autres Directives
- **gr_meetings_list.md**: Corréler les événements mentionnés avec les réunions
- **gr_international_events.md**: Identifier les événements annoncés dans les vidéos
- **Analyse stratégique**: Enrichir avec les insights des transcriptions

## Historique des Mises à Jour
- 2026-01-04: Création initiale de la directive
- 2026-01-04: Première extraction (306 vidéos identifiées)
