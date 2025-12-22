#!/usr/bin/env python3
"""
TextSpace Configuration Manager
Handles persistent config storage and example config management
"""

import os
import yaml
import shutil
from datetime import datetime
from pathlib import Path

class ConfigManager:
    """Manages persistent configuration with Railway volume support"""
    
    def __init__(self, persistent_path="/app/data", example_path="./config_examples"):
        self.persistent_path = Path(persistent_path)
        self.example_path = Path(example_path)
        self.config_types = ["rooms", "bots", "items", "scripts"]
        
        # Ensure directories exist
        self.persistent_path.mkdir(parents=True, exist_ok=True)
        self.example_path.mkdir(parents=True, exist_ok=True)
    
    def get_config_path(self, config_type: str, persistent: bool = True) -> Path:
        """Get path for config file"""
        base_path = self.persistent_path if persistent else self.example_path
        return base_path / f"{config_type}.yaml"
    
    def initialize_persistent_config(self):
        """Initialize persistent config from examples if not exists"""
        print("🔧 Initializing persistent configuration...")
        
        for config_type in self.config_types:
            persistent_file = self.get_config_path(config_type, persistent=True)
            example_file = self.get_config_path(config_type, persistent=False)
            repo_file = Path(f"{config_type}.yaml")
            
            if not persistent_file.exists():
                # Try to copy from example, then from repo
                source = example_file if example_file.exists() else repo_file
                if source.exists():
                    shutil.copy2(source, persistent_file)
                    print(f"  ✅ Initialized {config_type}.yaml from {source}")
                else:
                    print(f"  ⚠️  No source found for {config_type}.yaml")
            else:
                print(f"  ✅ {config_type}.yaml already exists in persistent storage")
    
    def update_examples_from_repo(self):
        """Update example configs from current repo files"""
        print("📝 Updating example configurations...")
        
        for config_type in self.config_types:
            repo_file = Path(f"{config_type}.yaml")
            example_file = self.get_config_path(config_type, persistent=False)
            
            if repo_file.exists():
                shutil.copy2(repo_file, example_file)
                print(f"  ✅ Updated example {config_type}.yaml")
            else:
                print(f"  ⚠️  Repo file {config_type}.yaml not found")
    
    def create_symlinks(self):
        """Create symlinks from repo location to persistent storage"""
        print("🔗 Creating symlinks to persistent storage...")
        
        for config_type in self.config_types:
            repo_file = Path(f"{config_type}.yaml")
            persistent_file = self.get_config_path(config_type, persistent=True)
            
            # Remove existing file/symlink
            if repo_file.exists() or repo_file.is_symlink():
                repo_file.unlink()
            
            # Create symlink
            repo_file.symlink_to(persistent_file.absolute())
            print(f"  ✅ Linked {config_type}.yaml → {persistent_file}")
    
    def backup_config(self, config_type: str) -> str:
        """Create timestamped backup of config"""
        persistent_file = self.get_config_path(config_type, persistent=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.persistent_path / f"{config_type}.yaml.backup.{timestamp}"
        
        if persistent_file.exists():
            shutil.copy2(persistent_file, backup_file)
            return str(backup_file)
        return ""
    
    def reset_config_with_confirmation(self, config_type: str, confirmation_code: str) -> dict:
        """Reset config to example with double confirmation"""
        expected_code = f"RESET_{config_type.upper()}_{datetime.now().strftime('%Y%m%d')}"
        
        if confirmation_code != expected_code:
            return {
                "success": False,
                "error": f"Invalid confirmation code. Expected: {expected_code}",
                "required_code": expected_code
            }
        
        # Create backup first
        backup_file = self.backup_config(config_type)
        
        # Reset from example
        persistent_file = self.get_config_path(config_type, persistent=True)
        example_file = self.get_config_path(config_type, persistent=False)
        
        if example_file.exists():
            shutil.copy2(example_file, persistent_file)
            return {
                "success": True,
                "message": f"Config {config_type} reset to example",
                "backup_created": backup_file
            }
        else:
            return {
                "success": False,
                "error": f"Example config {config_type}.yaml not found"
            }
    
    def get_config_info(self) -> dict:
        """Get information about all configs"""
        info = {
            "persistent_path": str(self.persistent_path),
            "example_path": str(self.example_path),
            "configs": {}
        }
        
        for config_type in self.config_types:
            persistent_file = self.get_config_path(config_type, persistent=True)
            example_file = self.get_config_path(config_type, persistent=False)
            
            info["configs"][config_type] = {
                "persistent_exists": persistent_file.exists(),
                "persistent_size": persistent_file.stat().st_size if persistent_file.exists() else 0,
                "example_exists": example_file.exists(),
                "last_modified": persistent_file.stat().st_mtime if persistent_file.exists() else 0
            }
        
        return info

if __name__ == "__main__":
    import sys
    
    manager = ConfigManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            manager.initialize_persistent_config()
        elif command == "update-examples":
            manager.update_examples_from_repo()
        elif command == "create-symlinks":
            manager.create_symlinks()
        elif command == "info":
            import json
            print(json.dumps(manager.get_config_info(), indent=2))
        elif command == "reset" and len(sys.argv) > 3:
            config_type = sys.argv[2]
            confirmation = sys.argv[3]
            result = manager.reset_config_with_confirmation(config_type, confirmation)
            print(json.dumps(result, indent=2))
        else:
            print("Usage: config_manager.py [init|update-examples|create-symlinks|info|reset <type> <code>]")
    else:
        print("🔧 TextSpace Configuration Manager")
        print("Available commands:")
        print("  init - Initialize persistent config from examples")
        print("  update-examples - Update examples from repo files")
        print("  create-symlinks - Link repo files to persistent storage")
        print("  info - Show configuration information")
        print("  reset <type> <code> - Reset config with confirmation")
