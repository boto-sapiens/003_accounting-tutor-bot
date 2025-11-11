import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Demo mode - makes admin panel accessible to everyone
DEMO_MODE = True

# Load YAML config
CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config():
    """Load configuration from YAML file"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

