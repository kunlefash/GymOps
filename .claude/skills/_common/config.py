"""
Configuration loader for agent skills.

Loads YAML config files from skill directories.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

# Try to import yaml, fall back to basic parsing if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# Cache for loaded configs
_config_cache: Dict[str, Dict] = {}


def _parse_simple_yaml(content: str) -> Dict:
    """Simple YAML-like parser for basic key-value configs."""
    result = {}
    current_dict = result
    current_key = None
    indent_stack = [(0, result)]
    
    for line in content.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        
        indent = len(line) - len(line.lstrip())
        
        if ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()
            
            # Adjust stack based on indent
            while indent_stack and indent <= indent_stack[-1][0]:
                indent_stack.pop()
            
            current_dict = indent_stack[-1][1] if indent_stack else result
            
            if value:
                # Simple key: value
                if value.startswith('[') and value.endswith(']'):
                    # List notation
                    items = value[1:-1].split(',')
                    current_dict[key] = [i.strip().strip('"\'') for i in items if i.strip()]
                elif value.startswith('"') or value.startswith("'"):
                    current_dict[key] = value.strip('"\'')
                elif value.isdigit():
                    current_dict[key] = int(value)
                elif value.lower() in ('true', 'false'):
                    current_dict[key] = value.lower() == 'true'
                else:
                    current_dict[key] = value
            else:
                # Nested dict
                current_dict[key] = {}
                indent_stack.append((indent + 2, current_dict[key]))
        elif stripped.startswith('- '):
            # List item
            if current_key and isinstance(current_dict.get(current_key), list):
                current_dict[current_key].append(stripped[2:].strip().strip('"\''))
    
    return result


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    path = Path(config_path)
    
    if not path.exists():
        return {}
    
    content = path.read_text()
    
    if HAS_YAML:
        return yaml.safe_load(content) or {}
    else:
        return _parse_simple_yaml(content)


def get_skill_config(skill_name: str, base_path: str = None) -> Dict[str, Any]:
    """
    Get configuration for a specific skill.
    
    Args:
        skill_name: Name of the skill (e.g., 'nuget-resolver')
        base_path: Base path to skills directory (auto-detected if None)
    
    Returns:
        Configuration dictionary
    """
    if skill_name in _config_cache:
        return _config_cache[skill_name]
    
    if base_path is None:
        # Try to find skills directory relative to this file
        this_dir = Path(__file__).parent
        base_path = this_dir.parent
    
    config_path = Path(base_path) / skill_name / 'config.yaml'
    config = load_config(str(config_path))
    
    _config_cache[skill_name] = config
    return config


def clear_cache():
    """Clear the configuration cache."""
    _config_cache.clear()
