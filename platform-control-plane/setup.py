#!/usr/bin/env python3
"""
Setup script for Platform Control Plane
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil


def setup():
    """Run complete setup for Platform Control Plane"""
    
    print("🚀 Platform Control Plane Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Create virtual environment
    print("\n📦 Creating virtual environment...")
    if Path("venv").exists():
        print("   Virtual environment already exists")
    else:
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        print("   ✅ Virtual environment created")
    
    # Determine pip path
    pip_path = Path("venv/Scripts/pip.exe") if os.name == 'nt' else Path("venv/bin/pip")
    
    # Install dependencies
    print("\n📚 Installing dependencies...")
    subprocess.run([str(pip_path), "install", "-r", "requirements.txt"])
    print("   ✅ Dependencies installed")
    
    # Create config directory if not exists
    config_dir = Path("config")
    if not config_dir.exists():
        print("\n⚙️ Creating config directory...")
        config_dir.mkdir()
        print("   ✅ Config directory created")
    
    # Check for config files
    print("\n🔍 Checking configuration files...")
    required_configs = ["domains.yml", "providers.yml", "policies.yml"]
    missing_configs = []
    
    for config_file in required_configs:
        config_path = config_dir / config_file
        example_path = config_dir / f"{config_file}.example"
        
        if not config_path.exists():
            if example_path.exists():
                shutil.copy(example_path, config_path)
                print(f"   📝 Created {config_file} from example")
            else:
                missing_configs.append(config_file)
                print(f"   ⚠️  {config_file} not found")
        else:
            print(f"   ✅ {config_file} exists")
    
    # Create logs directory
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("\n📄 Created logs directory")
    
    # Environment variables check
    print("\n🔐 Checking environment variables...")
    required_env_vars = [
        "PLATFORM_AWS_PROD_ROLE",
        "PLATFORM_AZURE_CLIENT_ID",
        "SENTINELONE_API_TOKEN"
    ]
    
    missing_env = []
    for var in required_env_vars:
        if os.environ.get(var):
            print(f"   ✅ {var} is set")
        else:
            missing_env.append(var)
            print(f"   ⚠️  {var} not set")
    
    # Create .env.example if needed
    env_example = Path(".env.example")
    if not env_example.exists():
        with open(env_example, 'w') as f:
            f.write("""# Platform Control Plane Environment Variables

# AWS
PLATFORM_AWS_PROD_ROLE=arn:aws:iam::654654560452:role/platform-control
PLATFORM_AWS_STAGING_ROLE=arn:aws:iam::381492229443:role/platform-control

# Azure
PLATFORM_AZURE_CLIENT_ID=your-client-id
PLATFORM_AZURE_CLIENT_SECRET=your-client-secret
PLATFORM_AZURE_TENANT_ID=your-tenant-id

# SentinelOne
SENTINELONE_API_TOKEN=your-api-token
SENTINELONE_ACCOUNT_ID=your-account-id

# Cisco
CISCO_ASA_USERNAME=admin
CISCO_ASA_PASSWORD=your-password
CISCO_ASA_ENABLE=your-enable-password

# Meraki
MERAKI_API_KEY=your-api-key
MERAKI_ORG_ID=your-org-id

# Notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
""")
        print("\n📝 Created .env.example file")
    
    # Summary
    print("\n" + "=" * 50)
    print("Setup Summary")
    print("=" * 50)
    
    if missing_configs:
        print(f"⚠️  Missing config files: {', '.join(missing_configs)}")
        print("   Please create these files based on the examples")
    
    if missing_env:
        print(f"⚠️  Missing environment variables: {', '.join(missing_env)}")
        print("   Copy .env.example to .env and fill in values")
    
    if not missing_configs and not missing_env:
        print("✅ Setup complete! You're ready to run the Platform Control Plane")
        print("\nTo start the server:")
        if os.name == 'nt':
            print("   .\\venv\\Scripts\\python -m mcp_server.main")
        else:
            print("   ./venv/bin/python -m mcp_server.main")
    else:
        print("\n⚠️  Please complete the configuration before running")
    
    # Create run script
    run_script = Path("run.sh") if os.name != 'nt' else Path("run.bat")
    if not run_script.exists():
        if os.name == 'nt':
            with open(run_script, 'w') as f:
                f.write("@echo off\n")
                f.write(".\\venv\\Scripts\\python -m mcp_server.main\n")
        else:
            with open(run_script, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("./venv/bin/python -m mcp_server.main\n")
            os.chmod(run_script, 0o755)
        print(f"\n📜 Created {run_script} for easy startup")


if __name__ == "__main__":
    setup()
