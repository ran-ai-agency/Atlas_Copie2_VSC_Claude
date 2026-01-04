# Directive: GR International - Constitution de la Liste des Réunions

## Objectif
Maintenir une liste JSON exhaustive de toutes les réunions du groupe Vaudreuil-Dorion 1, incluant les détails des liens enregistrés, pour permettre:
- L'analyse approfondie des performances du groupe
- La formulation de stratégies de recrutement
- La planification des activités futures
- Le suivi des tendances et métriques clés

## Contexte Utilisateur
- **Membre de**: GR International
- **Groupe**: Vaudreuil-Dorion 1 (virtuel)
- **Rôle**: Secrétaire-trésorier
- **URL du groupe**: `https://www.grinternational.ca/membres/reunions/?reunion=Vk14TmREYWFXM0dyVnhvV2RyOVFDMzQ3bEk4PTo6NWZiNjBhMzQ5NzQ3YTk4YWVjZTI0Y2Q4MzU4YWMwMjg`

## Inputs
- **Page des réunions**: URL encodée du groupe Vaudreuil-Dorion 1
- **Identifiants**: `GR_MEMBER_URL` dans `.env` (lien d'accès membre avec token)
- **Fréquence de mise à jour**: Hebdomadaire (après chaque nouvelle réunion)

## Structure des Données JSON

Le fichier JSON généré (`gr_vaudreuil_meetings.json`) suit cette structure:

```json
{
  "groupe": "Vaudreuil-Dorion 1",
  "derniere_mise_a_jour": "2026-01-04T00:30:00",
  "total_reunions": 68,
  "reunions": [
    {
      "date": "2025-12-18",
      "group": "Vaudreuil-Dorion 1",
      "present_count": 11,
      "absent_count": 1,
      "visitors_count": 6,
      "links_given": 0,
      "links_received": 0,
      "referrals_count": 21,
      "closed_business": 0.0,
      "transactions_count": 0,
      "members_present": ["Cormier, Nathalie (P)", "Sauvé, Mylène (VP)", "..."],
      "members_absent": ["Masse, Yvanhoé (DR)"],
      "visitors": [
        {
          "name": "Gibeau, Annie",
          "company": "Annie Gibeau Hypnose",
          "email": "hypnose.agibeau@outlook.com",
          "phone": "514-238-6108",
          "referred_by": "Nathalie Cormier (GD)",
          "is_member": false
        }
      ],
      "links": [
        {
          "member": "Sauvé, Mylène (VP)",
          "references": 2,
          "transactions": 0
        }
      ],
      "toolbox_presenter": "Cormier, Nathalie",
      "toolbox_subject": "Le grand reset de fin d'année : clarifier, aligner, planifier 2026",
      "total_attendees": 15,
      "form_completed_by": "Ranaivoarison, Roland",
      "notes": "Notes de la réunion",
      "detail_url": "/membres/reunions/consulter/?reunion=..."
    }
  ]
}
```

### Champs Détaillés

| Champ | Description |
|-------|-------------|
| `present_count` | Nombre de membres présents |
| `absent_count` | Nombre de membres absents |
| `visitors_count` | Nombre de visiteurs/invités |
| `referrals_count` | Total des références données par tous les membres |
| `transactions_count` | Nombre de transactions complétées |
| `members_present` | Liste des noms avec rôle (P=Président, VP=Vice-Président, etc.) |
| `visitors` | Liste détaillée des visiteurs avec coordonnées |
| `links` | Références par membre (nombre de références et transactions) |
| `toolbox_presenter` | Qui a présenté la boîte à outils GR |
| `toolbox_subject` | Sujet de la boîte à outils GR |
| `total_attendees` | Nombre total de participants (membres + visiteurs) |
| `form_completed_by` | Qui a rempli le rapport de réunion |

## Script/Outil
- `execution/gr_meetings_scraper.py` - Script Playwright pour l'extraction

### Utilisation

**Extraction complète (première fois ou reset):**
```bash
python execution/gr_meetings_scraper.py
```

**Extraction limitée (test avec 5 réunions):**
```bash
python execution/gr_meetings_scraper.py --max 5
```

**Mode visible (debug):**
```bash
python execution/gr_meetings_scraper.py --visible
```

**Ajouter une nouvelle réunion:**
```bash
python execution/gr_meetings_scraper.py --add 2026-01-08
```

## Outputs
1. **Fichier JSON principal**: `.tmp/gr_vaudreuil_meetings.json`
2. **Résumé Markdown**: `.tmp/gr_vaudreuil_summary.md`
3. **Captures d'écran**: `.tmp/gr_meetings_*.png`

## Étapes d'Exécution

### Extraction Initiale (Complète)
1. **Authentification**
   - Utiliser le lien membre avec token (`GR_MEMBER_URL`)
   - Vérifier l'accès au portail membres

2. **Navigation vers la page des réunions**
   - URL: `https://www.grinternational.ca/membres/reunions/?reunion=...`
   - Attendre le chargement du tableau

3. **Extraction de la liste**
   - Parser le tableau pour identifier toutes les dates
   - Récupérer les URLs "View/Consulter" pour chaque réunion

4. **Extraction des détails**
   - Pour chaque réunion, cliquer sur "View/Consulter"
   - Extraire: présences, absences, visiteurs
   - Extraire: liens donnés, liens reçus, référencements
   - Extraire: montant des affaires conclues
   - Extraire: liste des membres présents/absents
   - Extraire: détails des liens échangés

5. **Sauvegarde**
   - Générer le fichier JSON structuré
   - Générer le résumé Markdown

### Mise à Jour Hebdomadaire (Automatisée)

Les réunions du groupe Vaudreuil-Dorion 1 ont lieu chaque **jeudi matin**. L'extraction automatique est configurée pour s'exécuter chaque **vendredi à 7h00**.

#### Tâche Planifiée Windows
```powershell
# Créer la tâche planifiée
schtasks /create /tn "GR Meetings Weekly Update" /tr "c:\Users\ranai\Documents\Atlas - Copie\execution\gr_meetings_update.bat" /sc weekly /d FRI /st 07:00 /f
```

#### Script d'Exécution
Le fichier `execution/gr_meetings_update.bat` contient:
```batch
@echo off
cd /d "c:\Users\ranai\Documents\Atlas - Copie"
python execution/gr_meetings_scraper.py
```

#### Processus Manuel (si nécessaire)
1. **Vérifier la nouvelle réunion**
   - Identifier la date de la dernière réunion (généralement le jeudi précédent)
   - Si nouvelle réunion disponible, l'ajouter

2. **Exécuter avec --add** (pour une seule réunion spécifique)
   ```bash
   python execution/gr_meetings_scraper.py --add 2026-01-08
   ```

3. **Ou relancer une extraction complète**
   ```bash
   python execution/gr_meetings_scraper.py
   ```

4. **Vérifier les résultats**
   - Le JSON est mis à jour automatiquement
   - Le résumé est régénéré

## Cas d'Usage pour l'Analyse

### 1. Analyse des Performances
- Évolution du taux de présence
- Tendance des liens échangés
- Croissance des affaires conclues

### 2. Stratégies de Recrutement
- Identifier les périodes avec le plus de visiteurs
- Analyser les patterns de conversion visiteur -> membre
- Identifier les membres les plus actifs en termes de liens

### 3. Planification d'Activités
- Identifier les périodes creuses (vacances, été)
- Planifier des événements spéciaux
- Anticiper les besoins du groupe

## Métriques Clés à Suivre

| Métrique | Description | Objectif |
|----------|-------------|----------|
| Taux de présence | Présents / Total membres | > 80% |
| Liens par réunion | Moyenne des liens échangés | > 10 |
| Visiteurs/mois | Nombre de visiteurs mensuels | > 5 |
| Affaires conclues | Volume mensuel | Croissance |
| Taux de conversion | Visiteurs -> Membres | > 30% |

## Fréquence
- **Extraction complète**: À faire une fois (ou en cas de reset)
- **Mise à jour hebdomadaire**: Chaque vendredi après la réunion
- **Analyse mensuelle**: Premier du mois

## Cas Limites
- **Session expirée**: Le token `GR_MEMBER_URL` peut expirer. Régénérer depuis le site.
- **Réunion annulée**: Noter "annulée" dans les notes si applicable
- **Données manquantes**: Certaines anciennes réunions peuvent avoir des données incomplètes
- **Timeout**: Augmenter le délai si le site est lent

## Intégration avec Autres Directives
- **gr_international_events.md**: Utiliser les données pour recommander la participation aux événements
- **Zoho CRM**: Synchroniser les informations de membres si nécessaire
- **Rapports mensuels**: Générer des rapports de performance pour le groupe

## Historique des Mises à Jour
- 2026-01-03: Création initiale de la directive
- 2026-01-03: Implémentation du script gr_meetings_scraper.py
- 2026-01-04: Correction du parsing du tableau de présence (extraction des membres, références, transactions)
- 2026-01-04: Ajout de la gestion des retries et délais pour éviter le rate limiting
- 2026-01-04: Première extraction complète des 68 réunions (1457 références totales)
- 2026-01-04: Configuration de la tâche planifiée Windows "GR Meetings Weekly Update" (vendredi 7h00)
- 2026-01-04: Création du script gr_meetings_update.bat pour l'automatisation
