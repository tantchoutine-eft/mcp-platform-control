# MCP Performance Monitor
# Real-time monitoring and optimization for MCP servers

param(
    [int]$SampleInterval = 5,
    [int]$Duration = 60,
    [switch]$Export,
    [switch]$Continuous
)

Write-Host "`n🚀 MCP Performance Monitor" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan

$metrics = @{
    ServerLatency = @{}
    MemoryUsage = @{}
    ResponseTimes = @{}
    ErrorRates = @{}
}

function Test-ServerPerformance {
    param($ServerName, $TestCommand)
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $result = Invoke-Expression $TestCommand 2>&1
        $stopwatch.Stop()
        
        return @{
            Success = $true
            Latency = $stopwatch.ElapsedMilliseconds
            Timestamp = Get-Date
        }
    } catch {
        $stopwatch.Stop()
        return @{
            Success = $false
            Latency = $stopwatch.ElapsedMilliseconds
            Error = $_.Exception.Message
            Timestamp = Get-Date
        }
    }
}

function Get-ProcessMetrics {
    $uvProcesses = Get-Process -Name "python*", "node*", "uvx*" -ErrorAction SilentlyContinue
    
    $totalMemory = 0
    $totalCpu = 0
    $processCount = 0
    
    foreach ($proc in $uvProcesses) {
        if ($proc.CommandLine -like "*mcp-server*") {
            $totalMemory += $proc.WorkingSet64 / 1MB
            $totalCpu += $proc.CPU
            $processCount++
        }
    }
    
    return @{
        MemoryMB = [math]::Round($totalMemory, 2)
        CpuTime = [math]::Round($totalCpu, 2)
        ProcessCount = $processCount
    }
}

# Server test configurations
$serverTests = @(
    @{Name="AWS API"; Test="aws sts get-caller-identity --profile aws-sso-primary --output json"},
    @{Name="AWS S3"; Test="aws s3 ls --profile aws-sso-primary --page-size 1 --max-items 1"}
)

Write-Host "Monitoring for $Duration seconds (Sample every $SampleInterval sec)..."
Write-Host "Press Ctrl+C to stop`n"

$startTime = Get-Date
$samples = @()

do {
    $currentSample = @{
        Timestamp = Get-Date
        Servers = @{}
        System = Get-ProcessMetrics
    }
    
    # Test each server
    foreach ($test in $serverTests) {
        Write-Host "Testing $($test.Name)..." -NoNewline
        $result = Test-ServerPerformance -ServerName $test.Name -TestCommand $test.Test
        
        if ($result.Success) {
            Write-Host " ✅ $($result.Latency)ms" -ForegroundColor Green
        } else {
            Write-Host " ❌ Failed" -ForegroundColor Red
        }
        
        $currentSample.Servers[$test.Name] = $result
        
        # Update metrics
        if (-not $metrics.ServerLatency[$test.Name]) {
            $metrics.ServerLatency[$test.Name] = @()
        }
        $metrics.ServerLatency[$test.Name] += $result.Latency
    }
    
    # Display system metrics
    Write-Host "System: Memory: $($currentSample.System.MemoryMB)MB | Processes: $($currentSample.System.ProcessCount)"
    Write-Host "---"
    
    $samples += $currentSample
    
    if (-not $Continuous) {
        $elapsed = (Get-Date) - $startTime
        if ($elapsed.TotalSeconds -ge $Duration) { break }
    }
    
    Start-Sleep -Seconds $SampleInterval
    
} while ($true)

# Calculate statistics
Write-Host "`n📊 Performance Summary" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan

foreach ($serverName in $metrics.ServerLatency.Keys) {
    $latencies = $metrics.ServerLatency[$serverName]
    $avg = [math]::Round(($latencies | Measure-Object -Average).Average, 2)
    $min = ($latencies | Measure-Object -Minimum).Minimum
    $max = ($latencies | Measure-Object -Maximum).Maximum
    
    Write-Host "`n$serverName Performance:"
    Write-Host "  Average Latency: $avg ms"
    Write-Host "  Min/Max: $min ms / $max ms"
    
    if ($avg -lt 500) {
        Write-Host "  Status: ✅ Excellent" -ForegroundColor Green
    } elseif ($avg -lt 1000) {
        Write-Host "  Status: ⚠️ Good" -ForegroundColor Yellow
    } else {
        Write-Host "  Status: ❌ Needs Optimization" -ForegroundColor Red
    }
}

# Memory analysis
$avgMemory = [math]::Round(($samples.System.MemoryMB | Measure-Object -Average).Average, 2)
Write-Host "`nAverage Memory Usage: $avgMemory MB"

# Export results
if ($Export) {
    $exportData = @{
        StartTime = $startTime
        EndTime = Get-Date
        Duration = $Duration
        Samples = $samples
        Statistics = @{
            ServerLatencies = $metrics.ServerLatency
            AverageMemory = $avgMemory
        }
    }
    
    $exportPath = ".\logs\performance-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    New-Item -Path ".\logs" -ItemType Directory -Force | Out-Null
    $exportData | ConvertTo-Json -Depth 5 | Set-Content $exportPath
    Write-Host "`n📄 Performance data exported to: $exportPath" -ForegroundColor Gray
}

# Optimization recommendations
Write-Host "`n💡 Optimization Recommendations:" -ForegroundColor Cyan
$recommendations = @()

foreach ($serverName in $metrics.ServerLatency.Keys) {
    $avg = ($metrics.ServerLatency[$serverName] | Measure-Object -Average).Average
    if ($avg -gt 1000) {
        $recommendations += "• $serverName: Consider caching or connection pooling"
    }
}

if ($avgMemory -gt 500) {
    $recommendations += "• High memory usage detected. Consider restarting MCP servers"
}

if ($recommendations.Count -gt 0) {
    $recommendations | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
} else {
    Write-Host "  ✅ All systems performing optimally!" -ForegroundColor Green
}
