"""CAPSTONE PROJECT — Travel Assistant Agent.

This deliberately mirrors the travel-planner example from Module 1, so
you END where Module 1 BEGAN — but now you build it yourself.

It exercises every skill from both chapters:
  * custom tools (@tool + type hints + docstrings)
  * multiple tools that feed into each other
  * a pre-built community tool (calculator)
  * a system prompt
  * the agentic loop doing multi-step planning

WHAT TO WATCH: the agent calls get_weather_forecast FIRST, feeds those numbers
into suggest_packing_list, then prices the trip and compares to the budget.
Nobody wrote that sequence — the loop worked it out.

    python travel_assistant.py
    python travel_assistant.py "I'm going to Manali for 4 days, budget 15000"
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands_tools import calculator, file_write
from config import MODEL_ID


import requests
from typing import Dict, Any

@tool
def get_city_weather(city: str) -> dict:
    """
    Returns today's high, low and conditions for a city.
    
    Example output:
    {"high_c": 32, "low_c": 26, "conditions": "humid, occasional showers"}
    """
    
    # Step 1: Geocode city → lat/lon
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
    
    geo_res = requests.get(geo_url, params=geo_params, timeout=10)
    geo_data = geo_res.json()
    
    if not geo_data.get("results"):
        return {"error": f"City '{city}' not found"}
    
    location = geo_data["results"][0]
    lat = location["latitude"]
    lon = location["longitude"]
    
    # Step 2: Get today's daily forecast
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        "timezone": "auto",
        "forecast_days": 1
    }
    
    weather_res = requests.get(weather_url, params=weather_params, timeout=10)
    data = weather_res.json()["daily"]
    
    high = round(data["temperature_2m_max"][0])
    low = round(data["temperature_2m_min"][0])
    code = data["weather_code"][0]
    precip_prob = data["precipitation_probability_max"][0]
    
    # Simple human-readable conditions
    conditions_map = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "foggy",
        48: "foggy",
        51: "light drizzle",
        53: "drizzle",
        55: "heavy drizzle",
        61: "light rain",
        63: "moderate rain",
        65: "heavy rain",
        80: "rain showers",
        81: "moderate rain showers",
        82: "heavy rain showers",
        95: "thunderstorm",
        96: "thunderstorm with hail",
        99: "thunderstorm with heavy hail",
    }
    
    base = conditions_map.get(code, "unknown")
    
    # Add humidity/rain feel
    if precip_prob >= 50:
        conditions = f"humid, occasional showers"
    elif precip_prob >= 30:
        conditions = f"{base}, chance of showers"
    else:
        conditions = base
    
    return {
        "high_c": high,
        "low_c": low,
        "conditions": conditions
    }


@tool
def suggest_packing_list(high_c: int, low_c: int, days: int, conditions: str) -> list:
    """Suggest what to pack based on temperatures, trip length and conditions.

    Args:
        high_c: Daytime high in Celsius
        low_c: Night-time low in Celsius
        days: Number of days in the trip
        conditions: Short description of expected weather
    """
    items = [f"{days + 1} sets of clothes", "toiletries", "phone charger"]

    if high_c >= 30:
        items += ["light cotton clothing", "sunscreen", "sunglasses", "reusable water bottle"]
    if low_c <= 15:
        items += ["warm jacket", "thermal layer"]
    elif low_c <= 22:
        items += ["light jacket for evenings"]
    if "rain" in conditions.lower() or "shower" in conditions.lower():
        items += ["compact umbrella", "quick-dry footwear"]
    if "snow" in conditions.lower():
        items += ["gloves", "woollen cap", "waterproof boots"]

    return items


@tool
def estimate_trip_cost(city: str, days: int, travellers: int = 1) -> dict:
    """Estimate the cost of a trip in Indian rupees.

    Args:
        city: Destination city
        days: Number of days
        travellers: Number of people travelling (default: 1)
    """
    per_night = {"goa": 3500, "bangalore": 3000, "jaipur": 2500, "manali": 2800}
    stay = per_night.get(city.lower(), 3000) * days
    food = 1200 * days * travellers
    local_travel = 800 * days
    total = stay + food + local_travel

    return {
        "city": city,
        "days": days,
        "travellers": travellers,
        "stay_inr": stay,
        "food_inr": food,
        "local_travel_inr": local_travel,
        "total_inr": total,
    }


agent = Agent(
    model=BedrockModel(model_id=MODEL_ID),
    tools=[get_city_weather, suggest_packing_list, estimate_trip_cost, calculator],
    system_prompt=(
        "You are a practical travel assistant. "
        "When asked about a trip: check the weather first, then suggest what to pack "
        "based on that weather, then estimate the cost. "
        "Always say whether the trip fits the user's budget, and keep advice concise."
    ),
)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = (
            "I'm going to MANALI for 3 days with 2 friends. My budget is 20000 rupees. "
            "What should I pack, and does it fit my budget?"
        )

    print(f"\nQuestion: {question}\n" + "-" * 60)
    response = agent(question)
    print(response)