from typing import Final
from dotenv import load_dotenv
import os

load_dotenv()

# neo4j AuraDB credentials
NEO4J_INSTANCE_ID: Final[str] = os.getenv('NEO4J_INSTANCE_ID')
NEO4J_URI: Final[str] = os.getenv('NEO4J_URI')
NEO4J_USERNAME: Final[str] = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD: Final[str] = os.getenv('NEO4J_PASSWORD')