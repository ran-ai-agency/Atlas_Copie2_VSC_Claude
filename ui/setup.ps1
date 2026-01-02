# ===========================================
# Atlas UI - Script d'installation Windows
# ===========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ATLAS UI - Installation Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier Docker
Write-Host "[1/5] Vérification de Docker..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERREUR: Docker n'est pas installé!" -ForegroundColor Red
    Write-Host "Télécharger: https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Yellow
    exit 1
}
Write-Host "Docker OK: $dockerVersion" -ForegroundColor Green

# Créer .env si nécessaire
Write-Host ""
Write-Host "[2/5] Configuration de l'environnement..." -ForegroundColor Yellow

if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Fichier .env créé depuis .env.example" -ForegroundColor Green

    # Générer les clés de sécurité
    $credsKey = -join ((48..57) + (97..102) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    $credsIV = -join ((48..57) + (97..102) | Get-Random -Count 16 | ForEach-Object {[char]$_})
    $jwtSecret = -join ((48..57) + (97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})
    $jwtRefresh = -join ((48..57) + (97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})
    $meiliKey = -join ((48..57) + (97..102) | Get-Random -Count 32 | ForEach-Object {[char]$_})

    # Remplacer les placeholders
    $envContent = Get-Content ".env" -Raw
    $envContent = $envContent -replace "your_32_char_credentials_key_here", $credsKey
    $envContent = $envContent -replace "your_16_char_iv_here", $credsIV
    $envContent = $envContent -replace "your_jwt_secret_here_generate_random", $jwtSecret
    $envContent = $envContent -replace "your_jwt_refresh_secret_here", $jwtRefresh
    $envContent = $envContent -replace "atlas_search_key_change_me", $meiliKey
    Set-Content ".env" $envContent

    Write-Host "Clés de sécurité générées automatiquement" -ForegroundColor Green
} else {
    Write-Host "Fichier .env existe déjà" -ForegroundColor Green
}

# Demander les clés API
Write-Host ""
Write-Host "[3/5] Configuration des clés API..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Vous devez configurer les clés suivantes dans .env:" -ForegroundColor Cyan
Write-Host "  - ANTHROPIC_API_KEY (obligatoire)" -ForegroundColor White
Write-Host "  - MCP_NOTION_TOKEN (pour Notion)" -ForegroundColor White
Write-Host "  - MCP_ZOHO_*_KEY (pour Zoho)" -ForegroundColor White
Write-Host ""

$configure = Read-Host "Voulez-vous configurer maintenant? (o/n)"
if ($configure -eq "o" -or $configure -eq "O") {
    $anthropicKey = Read-Host "Clé API Anthropic (Claude)"
    if ($anthropicKey) {
        $envContent = Get-Content ".env" -Raw
        $envContent = $envContent -replace "your_anthropic_api_key_here", $anthropicKey
        Set-Content ".env" $envContent
        Write-Host "Clé Anthropic configurée" -ForegroundColor Green
    }
}

# Créer les dossiers
Write-Host ""
Write-Host "[4/5] Création des dossiers..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "images" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
Write-Host "Dossiers créés: images/, logs/" -ForegroundColor Green

# Lancer Docker
Write-Host ""
Write-Host "[5/5] Lancement de Atlas UI..." -ForegroundColor Yellow
Write-Host ""

$launch = Read-Host "Lancer Atlas UI maintenant? (o/n)"
if ($launch -eq "o" -or $launch -eq "O") {
    Write-Host "Téléchargement des images Docker..." -ForegroundColor Yellow
    docker-compose pull

    Write-Host "Démarrage des services..." -ForegroundColor Yellow
    docker-compose up -d

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   ATLAS UI est prêt!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Accès: http://localhost:3080" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Commandes utiles:" -ForegroundColor Yellow
    Write-Host "  docker-compose logs -f    # Voir les logs" -ForegroundColor White
    Write-Host "  docker-compose restart    # Redémarrer" -ForegroundColor White
    Write-Host "  docker-compose down       # Arrêter" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Pour lancer plus tard:" -ForegroundColor Yellow
    Write-Host "  cd ui" -ForegroundColor White
    Write-Host "  docker-compose up -d" -ForegroundColor White
}

Write-Host ""
Write-Host "Installation terminée!" -ForegroundColor Green
