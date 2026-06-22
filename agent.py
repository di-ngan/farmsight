import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import SequentialAgent
from agents.input_parser import input_parser_agent
from agents.coordinator import coordinator

root_agent = SequentialAgent(
    name="farmsight",
    description="FarmSight crop health diagnosis. Tell me your field coordinates and your crop question.",
    sub_agents=[input_parser_agent, coordinator],
)
