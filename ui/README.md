# Atlas UI - Interface Utilisateur

Interface web conviviale pour Atlas, basée sur LibreChat avec intégration Claude.

## Prérequis

- Docker et Docker Compose installés
- Clé API Anthropic (Claude)
- Tokens MCP pour Notion et Zoho

## Installation Rapide

### 1. Copier et configurer l'environnement

```bash
cp .env.example .env
```

Éditer `.env` avec vos clés:
- `ANTHROPIC_API_KEY` - Votre clé API Claude
- `MCP_NOTION_TOKEN` - Token Notion
- `MCP_ZOHO_*_KEY` - Clés MCP Zoho

### 2. Générer les clés de sécurité

```bash
# Générer CREDS_KEY (32 caractères hex)
openssl rand -hex 16

# Générer CREDS_IV (16 caractères hex)
openssl rand -hex 8

# Générer JWT_SECRET
openssl rand -hex 32

# Générer JWT_REFRESH_SECRET
openssl rand -hex 32
```

### 3. Lancer Atlas UI

```bash
docker-compose up -d
```

### 4. Accéder à l'interface

Ouvrir http://localhost:3080 dans votre navigateur.

## Structure des Fichiers

```
ui/
├── docker-compose.yml    # Configuration Docker
├── .env.example          # Template environnement
├── .env                  # Configuration (créer depuis example)
├── librechat.yaml        # Config LibreChat (modèles, MCP, presets)
├── images/               # Logo et images personnalisées
│   ├── logo.svg          # Logo Atlas
│   └── favicon.ico       # Favicon
└── logs/                 # Logs de l'application
```

## Personnalisation

### Changer le logo

Placer votre logo dans `images/logo.svg` (format SVG recommandé).

### Modifier les rôles/presets

Éditer la section `presets` dans `librechat.yaml` pour ajouter ou modifier les rôles Atlas.

### Ajouter des modèles

Modifier la section `endpoints.anthropic.models` dans `librechat.yaml`.

## Intégrations MCP

Atlas UI est pré-configuré pour:

| Service | Fonction |
|---------|----------|
| **Notion** | Documentation, projets, notes |
| **Zoho CRM** | Contacts, prospects, deals |
| **Zoho Books** | Finances, factures, dépenses |
| **Zoho Mail** | Emails, communications |

## Commandes Utiles

```bash
# Voir les logs
docker-compose logs -f atlas-ui

# Redémarrer
docker-compose restart

# Arrêter
docker-compose down

# Mise à jour
docker-compose pull && docker-compose up -d
```

## Sécurité

- Ne jamais commiter le fichier `.env`
- Utiliser des mots de passe forts pour JWT
- En production, configurer HTTPS avec un reverse proxy (nginx, traefik)

## Support

Pour toute question, contacter Ran.AI Agency.
