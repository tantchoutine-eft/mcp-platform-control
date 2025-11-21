# MCP Backup and Restore System
# Comprehensive backup, restore, and rollback functionality

param(
    [Parameter(ParameterSetName="Backup")]
    [switch]$Backup,
    
    [Parameter(ParameterSetName="Restore")]
    [switch]$Restore,
    
    [Parameter(ParameterSetName="List")]
    [switch]$List,
    
    [Parameter(ParameterSetName="Restore")]
    [string]$RestorePoint,
    
    [string]$Description = "",
    [switch]$AutoBackup
)

$backupDir = ".\backups"
$configPaths = @(
    @{Source="$env:USERPROFILE\.cursor\mcp.json"; Name="cursor-config"},
    @{Source=".\configs\mcp.json"; Name="project-config"},
    @{Source="$env:USERPROFILE\.aws\config"; Name="aws-config"},
    @{Source="$env:USERPROFILE\.aws\credentials"; Name="aws-credentials"}
)

Write-Host "`n💾 MCP Backup & Restore System" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

# Ensure backup directory exists
if (-not (Test-Path $backupDir)) {
    New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
}

function New-Backup {
    param([string]$Description)
    
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupName = "backup-$timestamp"
    $backupPath = Join-Path $backupDir $backupName
    
    Write-Host "`n📦 Creating backup: $backupName" -ForegroundColor Yellow
    if ($Description) {
        Write-Host "   Description: $Description" -ForegroundColor Gray
    }
    
    New-Item -Path $backupPath -ItemType Directory -Force | Out-Null
    
    $manifest = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Description = $Description
        Files = @()
        System = @{
            User = $env:USERNAME
            Computer = $env:COMPUTERNAME
            PowerShell = $PSVersionTable.PSVersion.ToString()
        }
    }
    
    foreach ($config in $configPaths) {
        if (Test-Path $config.Source) {
            $destFile = Join-Path $backupPath "$($config.Name).json"
            Copy-Item -Path $config.Source -Destination $destFile -Force
            
            $fileInfo = Get-Item $config.Source
            $manifest.Files += @{
                Name = $config.Name
                OriginalPath = $config.Source
                Size = $fileInfo.Length
                LastModified = $fileInfo.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                Hash = (Get-FileHash $config.Source -Algorithm SHA256).Hash
            }
            
            Write-Host "   ✅ Backed up: $($config.Name)" -ForegroundColor Green
        } else {
            Write-Host "   ⏭️ Skipped (not found): $($config.Name)" -ForegroundColor Gray
        }
    }
    
    # Save manifest
    $manifestPath = Join-Path $backupPath "manifest.json"
    $manifest | ConvertTo-Json -Depth 5 | Set-Content $manifestPath
    
    # Create verification hash
    $verificationHash = @{}
    Get-ChildItem $backupPath -Filter "*.json" | ForEach-Object {
        $verificationHash[$_.Name] = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    }
    $verificationPath = Join-Path $backupPath "verification.json"
    $verificationHash | ConvertTo-Json | Set-Content $verificationPath
    
    Write-Host "`n✅ Backup completed: $backupName" -ForegroundColor Green
    Write-Host "📁 Location: $backupPath" -ForegroundColor Gray
    
    # Cleanup old backups (keep last 10)
    $backups = Get-ChildItem $backupDir -Directory | Sort-Object Name -Descending
    if ($backups.Count -gt 10) {
        Write-Host "`n🧹 Cleaning old backups..." -ForegroundColor Yellow
        $toDelete = $backups | Select-Object -Skip 10
        foreach ($old in $toDelete) {
            Remove-Item $old.FullName -Recurse -Force
            Write-Host "   Removed: $($old.Name)" -ForegroundColor Gray
        }
    }
    
    return $backupName
}

function Get-Backups {
    $backups = Get-ChildItem $backupDir -Directory | Sort-Object Name -Descending
    
    if ($backups.Count -eq 0) {
        Write-Host "`n⚠️ No backups found" -ForegroundColor Yellow
        return $null
    }
    
    Write-Host "`n📋 Available Backups:" -ForegroundColor Cyan
    Write-Host "=====================" -ForegroundColor Cyan
    
    $backupList = @()
    $index = 1
    
    foreach ($backup in $backups) {
        $manifestPath = Join-Path $backup.FullName "manifest.json"
        
        if (Test-Path $manifestPath) {
            $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
            
            Write-Host "`n[$index] $($backup.Name)" -ForegroundColor Yellow
            Write-Host "    Created: $($manifest.Timestamp)"
            if ($manifest.Description) {
                Write-Host "    Description: $($manifest.Description)" -ForegroundColor Gray
            }
            Write-Host "    Files: $($manifest.Files.Count)"
            
            $backupList += @{
                Index = $index
                Name = $backup.Name
                Path = $backup.FullName
                Manifest = $manifest
            }
            
            $index++
        }
    }
    
    return $backupList
}

function Restore-Backup {
    param([string]$BackupIdentifier)
    
    # Find backup
    $backupPath = $null
    $manifest = $null
    
    if (Test-Path (Join-Path $backupDir $BackupIdentifier)) {
        # Direct backup name provided
        $backupPath = Join-Path $backupDir $BackupIdentifier
    } else {
        # Try to find by index or pattern
        $backups = Get-Backups
        if ($backups) {
            if ($BackupIdentifier -match '^\d+$') {
                # Index provided
                $selected = $backups | Where-Object { $_.Index -eq [int]$BackupIdentifier }
                if ($selected) {
                    $backupPath = $selected.Path
                    $manifest = $selected.Manifest
                }
            } else {
                # Pattern match
                $selected = $backups | Where-Object { $_.Name -like "*$BackupIdentifier*" } | Select-Object -First 1
                if ($selected) {
                    $backupPath = $selected.Path
                    $manifest = $selected.Manifest
                }
            }
        }
    }
    
    if (-not $backupPath -or -not (Test-Path $backupPath)) {
        Write-Host "❌ Backup not found: $BackupIdentifier" -ForegroundColor Red
        return $false
    }
    
    # Load manifest if not already loaded
    if (-not $manifest) {
        $manifestPath = Join-Path $backupPath "manifest.json"
        if (Test-Path $manifestPath) {
            $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
        }
    }
    
    Write-Host "`n🔄 Restoring from backup: $(Split-Path $backupPath -Leaf)" -ForegroundColor Yellow
    if ($manifest.Description) {
        Write-Host "   Description: $($manifest.Description)" -ForegroundColor Gray
    }
    
    # Verify backup integrity
    Write-Host "`n🔍 Verifying backup integrity..." -ForegroundColor Cyan
    $verificationPath = Join-Path $backupPath "verification.json"
    if (Test-Path $verificationPath) {
        $verification = Get-Content $verificationPath -Raw | ConvertFrom-Json
        $integrityOk = $true
        
        foreach ($file in $verification.PSObject.Properties) {
            $filePath = Join-Path $backupPath $file.Name
            if (Test-Path $filePath) {
                $currentHash = (Get-FileHash $filePath -Algorithm SHA256).Hash
                if ($currentHash -ne $file.Value) {
                    Write-Host "   ❌ Integrity check failed: $($file.Name)" -ForegroundColor Red
                    $integrityOk = $false
                }
            }
        }
        
        if (-not $integrityOk) {
            Write-Host "`n⚠️ Backup integrity compromised. Continue anyway? (Y/N): " -NoNewline -ForegroundColor Yellow
            $response = Read-Host
            if ($response -ne 'Y' -and $response -ne 'y') {
                Write-Host "Restore cancelled." -ForegroundColor Yellow
                return $false
            }
        } else {
            Write-Host "   ✅ Integrity verified" -ForegroundColor Green
        }
    }
    
    # Create pre-restore backup
    Write-Host "`n📸 Creating pre-restore snapshot..." -ForegroundColor Cyan
    $snapshotName = New-Backup -Description "Pre-restore snapshot (before restoring $(Split-Path $backupPath -Leaf))"
    
    # Perform restoration
    Write-Host "`n🚀 Restoring files..." -ForegroundColor Yellow
    $restored = 0
    $failed = 0
    
    foreach ($fileInfo in $manifest.Files) {
        $sourceFile = Join-Path $backupPath "$($fileInfo.Name).json"
        $destFile = $fileInfo.OriginalPath
        
        if (Test-Path $sourceFile) {
            try {
                # Ensure destination directory exists
                $destDir = Split-Path $destFile -Parent
                if ($destDir -and -not (Test-Path $destDir)) {
                    New-Item -Path $destDir -ItemType Directory -Force | Out-Null
                }
                
                Copy-Item -Path $sourceFile -Destination $destFile -Force
                Write-Host "   ✅ Restored: $($fileInfo.Name)" -ForegroundColor Green
                $restored++
            } catch {
                Write-Host "   ❌ Failed: $($fileInfo.Name) - $_" -ForegroundColor Red
                $failed++
            }
        } else {
            Write-Host "   ⚠️ Source not found: $($fileInfo.Name)" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n📊 Restore Summary:" -ForegroundColor Cyan
    Write-Host "   Restored: $restored files" -ForegroundColor Green
    if ($failed -gt 0) {
        Write-Host "   Failed: $failed files" -ForegroundColor Red
    }
    Write-Host "   Snapshot: $snapshotName" -ForegroundColor Gray
    
    if ($failed -eq 0) {
        Write-Host "`n✅ Restore completed successfully!" -ForegroundColor Green
        Write-Host "💡 Restart Cursor IDE to apply changes" -ForegroundColor Yellow
        return $true
    } else {
        Write-Host "`n⚠️ Restore completed with errors" -ForegroundColor Yellow
        Write-Host "💡 You can rollback using: .\backup-restore.ps1 -Restore -RestorePoint '$snapshotName'" -ForegroundColor Cyan
        return $false
    }
}

# Auto-backup functionality
if ($AutoBackup) {
    Write-Host "`n⏰ Setting up auto-backup..." -ForegroundColor Cyan
    
    $taskName = "MCP-AutoBackup"
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$(Get-Location)\scripts\backup-restore.ps1`" -Backup -Description 'Automated daily backup'"
    $trigger = New-ScheduledTaskTrigger -Daily -At "2:00AM"
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    try {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
        Write-Host "✅ Auto-backup scheduled for daily at 2:00 AM" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to schedule auto-backup: $_" -ForegroundColor Red
    }
}

# Main execution
if ($Backup) {
    New-Backup -Description $Description
} elseif ($Restore) {
    if (-not $RestorePoint) {
        # Interactive restore
        $backups = Get-Backups
        if ($backups) {
            Write-Host "`nSelect backup to restore (number or name): " -NoNewline -ForegroundColor Cyan
            $selection = Read-Host
            Restore-Backup -BackupIdentifier $selection
        }
    } else {
        Restore-Backup -BackupIdentifier $RestorePoint
    }
} elseif ($List) {
    Get-Backups
} else {
    # Show usage
    Write-Host "`nUsage:" -ForegroundColor Yellow
    Write-Host "  Backup:  .\backup-restore.ps1 -Backup [-Description 'description']"
    Write-Host "  Restore: .\backup-restore.ps1 -Restore [-RestorePoint 'backup-name']"
    Write-Host "  List:    .\backup-restore.ps1 -List"
    Write-Host "  Auto:    .\backup-restore.ps1 -AutoBackup"
    Write-Host "`nExamples:" -ForegroundColor Cyan
    Write-Host "  .\backup-restore.ps1 -Backup -Description 'Before major update'"
    Write-Host "  .\backup-restore.ps1 -Restore -RestorePoint 'backup-20241115-143022'"
    Write-Host "  .\backup-restore.ps1 -List"
}
