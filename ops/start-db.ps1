param([switch]$Initialize)
$ErrorActionPreference = 'Stop'
$radarProject = Split-Path -Parent $PSScriptRoot
$radarPrivate = if ($env:RADAR_PRIVATE_ROOT) { $env:RADAR_PRIVATE_ROOT } else { Join-Path $env:LOCALAPPDATA 'RadarDeEditais' }
$radarSecrets = Join-Path $radarPrivate 'secrets'
$radarAbsolute = [IO.Path]::GetFullPath($radarPrivate)
$radarProtected = @([IO.Path]::GetFullPath($radarProject))
$radarAncestor = [IO.DirectoryInfo]::new($radarProject).Parent
while ($null -ne $radarAncestor) {
    if ((Test-Path -LiteralPath (Join-Path $radarAncestor.FullName 'MANUAL_DO_BRAIN.md')) -and (Test-Path -LiteralPath (Join-Path $radarAncestor.FullName 'SEGURANCA.md'))) { $radarProtected += $radarAncestor.FullName }
    $radarAncestor = $radarAncestor.Parent
}
foreach ($radarProtectedPath in $radarProtected) {
    if ($radarAbsolute.Equals($radarProtectedPath, [StringComparison]::OrdinalIgnoreCase) -or $radarAbsolute.StartsWith($radarProtectedPath.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Credenciais devem ficar fora do projeto e do Brain.' }
}
if ($radarAbsolute -match 'OneDrive') { throw 'Credenciais devem ficar fora do OneDrive.' }
New-Item -ItemType Directory -Force -Path $radarSecrets | Out-Null
# Diretório privado: acesso apenas ao usuário atual e SYSTEM.
$radarAcl = Get-Acl -LiteralPath $radarPrivate
$radarAcl.SetAccessRuleProtection($true, $false)
foreach ($radarAccess in @($radarAcl.Access)) { $radarAcl.RemoveAccessRuleSpecific($radarAccess) }
$radarCurrent = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
foreach ($radarSid in @($radarCurrent, [System.Security.Principal.SecurityIdentifier]'S-1-5-18')) {
    $radarRule = New-Object System.Security.AccessControl.FileSystemAccessRule($radarSid,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
    $radarAcl.AddAccessRule($radarRule)
}
$radarDirectory = [IO.DirectoryInfo]::new($radarPrivate)
[IO.FileSystemAclExtensions]::SetAccessControl($radarDirectory, $radarAcl)
foreach ($radarName in @('admin_password','loader_password')) {
    $radarSecret = Join-Path $radarSecrets $radarName
    if (-not (Test-Path -LiteralPath $radarSecret)) {
        $radarBytes = New-Object byte[] 32
        [System.Security.Cryptography.RandomNumberGenerator]::Fill($radarBytes)
        [IO.File]::WriteAllText($radarSecret, [Convert]::ToBase64String($radarBytes), [Text.UTF8Encoding]::new($false))
    }
}
$env:RADAR_DB_SECRET_FILE = Join-Path $radarSecrets 'admin_password'
Push-Location $radarProject
try {
    docker compose config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Compose inválido' }
    docker compose up -d --wait db
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao iniciar o banco' }
    if ($Initialize) {
        & '.venv/Scripts/python.exe' -m radar.cli init-db
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao inicializar schema' }
    }
} finally {
    Pop-Location
    Remove-Item Env:RADAR_DB_SECRET_FILE -ErrorAction SilentlyContinue
}
