# run.ps1 — common task runner for ICSE 2027 codebase
# Usage: .\run.ps1 <command> [args]

param(
    [Parameter(Position=0)][string]$cmd = "help",
    [Parameter(Position=1)][string]$method = "",
    [Parameter(Position=2)][string]$benchmark = "hg2k_smoke",
    [Parameter(Position=3)][string]$backbone = "gemma2-9b",
    [int]$seed = 0
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host @"
ICSE 2027 task runner

  .\run.ps1 preflight                          - check Docker + Ollama + paths
  .\run.ps1 preflight-llm                      - + LLM round-trip
  .\run.ps1 preflight-full <snippet_id>        - + end-to-end on a snippet
  .\run.ps1 docker-check                       - verbose Docker setup verification
  .\run.ps1 setup-check                        - all-in-one setup verification

  Standard run sequence (~3-4h on hg2k_20pct):
  .\run.ps1 run-baselines                      - m0/m1/m2 on hg2k_20pct (~3 min)
  .\run.ps1 run-cascade                        - m10 on hg2k_20pct (~3 min)
  .\run.ps1 run-agentic                        - m11/m12/m13/m14 on hg2k_20pct (~2-3h)

  .\run.ps1 headline                           - reproduce paper headline (m10, ~5 min)
  .\run.ps1 baselines                          - run m0/m1/m2 on hg2k_full (~1 min)
  .\run.ps1 method <method> <benchmark>        - generic run
  .\run.ps1 progress <method> <benchmark>      - live progress watcher
  .\run.ps1 compare                            - ablation table m10..m14
  .\run.ps1 summary                            - all runs overview (md table)
  .\run.ps1 summary <benchmark>                - filter to one benchmark

  Examples:
    .\run.ps1 method m11_agentic_orchestrator hg2k_smoke
    .\run.ps1 method m10_heterogeneous_cascade hg2k_full
    .\run.ps1 progress m11_agentic_orchestrator hg2k_smoke

Defaults: backbone=gemma2-9b, seed=0, benchmark=hg2k_smoke
"@
}

function Run-Method {
    param([string]$m, [string]$b, [string]$bb)
    Write-Host "`n=== Running $m on $b ($bb, seed=$seed) ===" -ForegroundColor Cyan
    python -m research.icse27.run_experiment `
        --method $m `
        --backbone $bb `
        --benchmark $b `
        --seed $seed `
        --resume
}

function Show-Progress {
    param([string]$m, [string]$b, [string]$bb)
    $dir = "results/icse27/$m/$bb/$b/seed$seed"
    Write-Host "Watching $dir`n" -ForegroundColor Cyan
    python -m research.icse27.analyze.progress --run $dir
}

switch ($cmd) {
    "help"            { Show-Help }
    "preflight"       { python -m research.icse27.preflight }
    "preflight-llm"   { python -m research.icse27.preflight --backbone gemma2-9b }
    "preflight-full" {
        $sn = if ($method) { $method } else { "sample_100" }
        python -m research.icse27.preflight --backbone gemma2-9b --snippet $sn
    }
    "docker-check" {
        Write-Host "`n=== Docker setup verification ===" -ForegroundColor Cyan
        Write-Host "`n[1] docker version:"
        docker version --format "  Client: {{.Client.Version}}`n  Server: {{.Server.Version}}"
        if ($LASTEXITCODE -ne 0) { Write-Host "  FAIL: Docker Desktop not running" -ForegroundColor Red; return }
        Write-Host "`n[2] docker info (disk usage):"
        docker system df 2>$null | Select-Object -First 5
        Write-Host "`n[3] test build python:3.10 image:"
        docker pull python:3.10-slim 2>$null | Select-Object -Last 1
        Write-Host "`n[4] test minimal build:"
        $tmp = New-TemporaryFile
        Remove-Item $tmp
        $tmpDir = New-Item -Type Directory -Path "$($tmp.FullName)_dir" -Force
        @"
FROM python:3.10-slim
RUN echo 'icse27-docker-check'
"@ | Out-File "$tmpDir\Dockerfile" -Encoding utf8 -NoNewline
        docker build -t icse27/check:latest $tmpDir 2>&1 | Select-Object -Last 3
        docker rmi icse27/check:latest 2>$null | Out-Null
        Remove-Item -Recurse $tmpDir -Force
        Write-Host "`n[5] disk image path (move if filling C:):"
        $info = docker info --format "{{.DockerRootDir}}" 2>$null
        Write-Host "  $info"
        Write-Host "`nDocker setup: OK" -ForegroundColor Green
    }
    "setup-check" {
        Write-Host "`n=== Full setup verification ===" -ForegroundColor Cyan
        Write-Host "`n--- 1. Docker ---"
        & $PSCommandPath docker-check
        Write-Host "`n--- 2. Ollama ---"
        ollama list 2>$null | Select-Object -First 5
        if ($LASTEXITCODE -ne 0) { Write-Host "  FAIL: Ollama not running. Start it via Start menu or 'ollama serve'." -ForegroundColor Red }
        Write-Host "`n--- 3. Python harness ---"
        python -m research.icse27.preflight --backbone gemma2-9b
    }
    "run-baselines" {
        foreach ($m in @("m0_pllm_replay","m1_memres_replay","m2_cgar_rule_replay")) {
            Run-Method $m "hg2k_20pct" "none"
        }
        python -m research.icse27.analyze.summary_table --benchmark hg2k_20pct
    }
    "run-cascade" {
        Run-Method "m10_heterogeneous_cascade" "hg2k_20pct" "none"
        python -m research.icse27.analyze.summary_table --benchmark hg2k_20pct
    }
    "run-agentic" {
        foreach ($m in @("m11_agentic_orchestrator","m12_mutation_ensemble","m13_swarm_proposer","m14_snippet_rewriting")) {
            Run-Method $m "hg2k_20pct" "gemma2-9b"
        }
        python -m research.icse27.analyze.summary_table --benchmark hg2k_20pct
    }
    "headline" {
        Write-Host "`n=== Reproducing paper headline (m10 cascade, no Docker, no LLM) ===" -ForegroundColor Green
        Run-Method "m10_heterogeneous_cascade" "hg2k_full" "none"
        Run-Method "m10_heterogeneous_cascade" "gitchameleon" "none"
        Write-Host "`nResults:" -ForegroundColor Green
        python -m research.icse27.analyze.ablation_table --csvs `
            results/icse27/m10_heterogeneous_cascade/none/hg2k_full/seed0/results.csv `
            results/icse27/m10_heterogeneous_cascade/none/gitchameleon/seed0/results.csv
    }
    "baselines" {
        foreach ($m in @("m0_pllm_replay","m1_memres_replay","m2_cgar_rule_replay")) {
            Run-Method $m "hg2k_full" "none"
        }
        python -m research.icse27.analyze.ablation_table --csvs `
            results/icse27/m0_pllm_replay/none/hg2k_full/seed0/results.csv `
            results/icse27/m1_memres_replay/none/hg2k_full/seed0/results.csv `
            results/icse27/m2_cgar_rule_replay/none/hg2k_full/seed0/results.csv
    }
    "method" {
        if (-not $method) { Write-Host "Usage: .\run.ps1 method <method_name> [benchmark]"; exit 1 }
        $bb = if ($method -like "m0*" -or $method -like "m1_*" -or $method -like "m2_*" -or $method -like "m10*") { "none" } else { "gemma2-9b" }
        Run-Method $method $benchmark $bb
    }
    "progress" {
        if (-not $method) { Write-Host "Usage: .\run.ps1 progress <method_name> [benchmark]"; exit 1 }
        $bb = if ($method -like "m0*" -or $method -like "m1_*" -or $method -like "m2_*" -or $method -like "m10*") { "none" } else { "gemma2-9b" }
        Show-Progress $method $benchmark $bb
    }
    "summary" {
        $bench = if ($method) { $method } else { "" }
        if ($bench) {
            python -m research.icse27.analyze.summary_table --benchmark $bench
        } else {
            python -m research.icse27.analyze.summary_table
        }
    }
    "compare" {
        Write-Host "`n=== Method comparison on hg2k_full ===" -ForegroundColor Cyan
        $csvs = @(
            "results/icse27/m0_pllm_replay/none/hg2k_full/seed0/results.csv",
            "results/icse27/m1_memres_replay/none/hg2k_full/seed0/results.csv",
            "results/icse27/m2_cgar_rule_replay/none/hg2k_full/seed0/results.csv",
            "results/icse27/m10_heterogeneous_cascade/none/hg2k_full/seed0/results.csv",
            "results/icse27/m11_agentic_orchestrator/gemma2-9b/hg2k_full/seed0/results.csv",
            "results/icse27/m12_mutation_ensemble/gemma2-9b/hg2k_full/seed0/results.csv",
            "results/icse27/m13_swarm_proposer/gemma2-9b/hg2k_full/seed0/results.csv",
            "results/icse27/m14_snippet_rewriting/gemma2-9b/hg2k_full/seed0/results.csv"
        )
        $existing = $csvs | Where-Object { Test-Path $_ }
        if ($existing.Count -eq 0) {
            Write-Host "No results found on hg2k_full. Run methods first." -ForegroundColor Yellow
        } else {
            python -m research.icse27.analyze.ablation_table --csvs @existing
        }
    }
    default {
        Write-Host "Unknown command: $cmd`n" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
