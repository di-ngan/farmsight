import datetime

from google.adk.agents import ParallelAgent, SequentialAgent

from agents.remote_sensing import remote_sensing_agent
from agents.weather_agent import weather_agent
from agents.synthesis import synthesis_agent


def get_season(d: datetime.date | None = None) -> str:
    d = d or datetime.date.today()
    return "kharif" if 6 <= d.month <= 10 else "rabi"


def get_sowing_default(season: str, year: int) -> datetime.date:
    return datetime.date(year, 6, 1) if season == "kharif" else datetime.date(year, 11, 1)


def days_after_sowing(season: str, today: datetime.date | None = None) -> int:
    today = today or datetime.date.today()
    sowing = get_sowing_default(season, today.year)
    # if sowing is in the future (e.g. rabi hasn't started yet) use previous year
    if sowing > today:
        sowing = get_sowing_default(season, today.year - 1)
    return max(0, (today - sowing).days)


_data_gathering = ParallelAgent(
    name="data_gathering",
    description="Fetches NDVI and rainfall data simultaneously",
    sub_agents=[remote_sensing_agent, weather_agent],
)

coordinator = SequentialAgent(
    name="farmsight_coordinator",
    description="Orchestrates remote sensing, weather, and synthesis agents to diagnose crop stress",
    sub_agents=[_data_gathering, synthesis_agent],
)
