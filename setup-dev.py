#!/usr/bin/env python3
"""
Development setup script for Viral Together application.

This script helps set up the development environment with all necessary
dependencies and configurations for testing.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    if description:
        print(f"🔧 {description}")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        return False
    
    print("✅ Success!")
    return True


def install_dependencies(enhanced=False):
    """Install project dependencies."""
    print("📦 Installing dependencies...")
    
    # Install core dependencies
    if not run_command(["pip", "install", "-r", "requirements.txt"], 
                      "Installing core dependencies"):
        return False
    
    # Install enhanced testing tools if requested
    if enhanced:
        if not run_command(["pip", "install", "-r", "requirements-test.txt"],
                          "Installing enhanced testing tools"):
            return False
    
    return True


def setup_environment():
    """Set up environment variables and configuration."""
    print("🌍 Setting up environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating .env file...")
        env_content = """# Development Environment Variables
TESTING=true
TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
        env_file.write_text(env_content)
        print("✅ Created .env file with default values")
    else:
        print("✅ .env file already exists")


def setup_pre_commit():
    """Set up pre-commit hooks."""
    print("🪝 Setting up pre-commit hooks...")
    
    # Create .pre-commit-config.yaml if it doesn't exist
    pre_commit_config = Path(".pre-commit-config.yaml")
    if not pre_commit_config.exists():
        config_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]
"""
        pre_commit_config.write_text(config_content)
        print("✅ Created .pre-commit-config.yaml")
    
    # Install pre-commit hooks
    if run_command(["pre-commit", "install"], "Installing pre-commit hooks"):
        print("✅ Pre-commit hooks installed")
    else:
        print("⚠️  Pre-commit installation failed (optional)")


def run_initial_tests():
    """Run a basic test to verify setup."""
    print("🧪 Running initial tests to verify setup...")
    
    # Run a simple test
    result = subprocess.run([
        "python", "-m", "pytest", 
        "tests/unit/test_auth.py::TestPasswordSecurity::test_password_hashing_works",
        "-v"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Initial test passed! Setup is working correctly.")
        return True
    else:
        print("❌ Initial test failed. There might be an issue with the setup.")
        print("Error output:")
        print(result.stdout)
        print(result.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Set up Viral Together development environment")
    
    parser.add_argument(
        "--enhanced", 
        action="store_true",
        help="Install enhanced testing and development tools"
    )
    parser.add_argument(
        "--skip-test", 
        action="store_true",
        help="Skip running initial tests"
    )
    parser.add_argument(
        "--no-pre-commit", 
        action="store_true",
        help="Skip setting up pre-commit hooks"
    )
    
    args = parser.parse_args()
    
    print("🚀 Setting up Viral Together development environment...")
    print("=" * 60)
    
    # Step 1: Install dependencies
    if not install_dependencies(enhanced=args.enhanced):
        print("❌ Failed to install dependencies")
        return 1
    
    # Step 2: Set up environment
    setup_environment()
    
    # Step 3: Set up pre-commit (optional)
    if not args.no_pre_commit:
        setup_pre_commit()
    
    # Step 4: Run initial tests (optional)
    if not args.skip_test:
        if not run_initial_tests():
            print("\n⚠️  Setup completed but tests failed.")
            print("You may need to check your configuration.")
            return 1
    
    print("\n" + "=" * 60)
    print("🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("1. Review the .env file and update values as needed")
    print("2. Run tests: python run_tests.py")
    print("3. Start development: uvicorn app.main:app --reload")
    
    if args.enhanced:
        print("4. Use code formatting: black . && isort .")
        print("5. Run linting: flake8 .")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 