$IMAGE_NAME = "ghcr.io/walterrosa2/elos_email_inteligente:latest"

function Build-Image {
    Write-Host "🚧 Iniciando Build da imagem: $IMAGE_NAME..." -ForegroundColor Yellow
    docker build -t $IMAGE_NAME .
    if ($?) { Write-Host "✅ Build concluído com sucesso!" -ForegroundColor Green }
    else { Write-Host "❌ Falha no Build." -ForegroundColor Red }
}

function Push-Image {
    Write-Host "⬆️ Enviando imagem para o GitHub Container Registry..." -ForegroundColor Yellow
    docker push $IMAGE_NAME
    if ($?) { Write-Host "✅ Push concluído!" -ForegroundColor Green }
    else { Write-Host "❌ Falha no Push. Verifique se você fez login (docker login ghcr.io)." -ForegroundColor Red }
}

function Deploy-App {
    Write-Host "🚀 Iniciando aplicação com Docker Compose..." -ForegroundColor Yellow
    docker-compose up -d
    if ($?) { Write-Host "✅ Aplicação iniciada em http://localhost:8501" -ForegroundColor Green }
    else { Write-Host "❌ Falha ao iniciar." -ForegroundColor Red }
}

function Stop-App {
    Write-Host "🛑 Parando aplicação..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Aplicação parada." -ForegroundColor Green
}

function Show-Menu {
    Clear-Host
    Write-Host "=== GESTÃO DE DEPLOY DOCKER (ELOS) ===" -ForegroundColor Cyan
    Write-Host "1. Build Imagem"
    Write-Host "2. Push Imagem (GHCR)"
    Write-Host "3. Rodar Aplicação (Docker Compose)"
    Write-Host "4. Parar Aplicação"
    Write-Host "5. Logs da Aplicação"
    Write-Host "0. Sair"
}

do {
    Show-Menu
    $choice = Read-Host "Escolha uma opção"
    switch ($choice) {
        "1" { Build-Image; Pause }
        "2" { Push-Image; Pause }
        "3" { Deploy-App; Pause }
        "4" { Stop-App; Pause }
        "5" { docker-compose logs -f; Pause }
        "0" { Write-Host "Saindo..."; break }
        default { Write-Host "Opção inválida." -ForegroundColor Red; Pause }
    }
} until ($choice -eq "0")
