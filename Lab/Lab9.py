import asyncio
import os
import time

import requests
import streamlit as st
from agents import Agent, Runner, function_tool

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
MODEL = "gpt-5-mini"

st.title("What to Wear: Multi-Agent Crew")

@st.cache_data(ttl=600)
def get_weather_data(location):
    url = f'https://wttr.in/{location}?format=j1'
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        raise Exception(f'wttr.in error: status {response.status_code}')
    try:
        data = response.json()
    except ValueError:
        raise Exception(f'Could not find a location named {location}')
    current = data['current_condition'][0]
    today = data['weather'][0]

    time_labels = {'900': '9am', '1200': '12pm', '1500': '3pm', '1800': '6pm'}

    current_snapshot = {
        'temp_f': float(current['temp_F']),
        'feels_like_f': float(current['FeelsLikeF']),
        'description': current['weatherDesc'][0]['value']
    }

    forecast = {}
    for hour in today['hourly']:
        if hour['time'] in time_labels:
            label = time_labels[hour['time']]
            forecast[label] = {
                'feels_like_f': float(hour['FeelsLikeF']),
                'chance_of_rain': int(hour['chanceofrain']),
                'chance_of_sunshine': int(hour['chanceofsunshine']),
                'wind_gust_miles': float(hour['WindGustMiles']),
                'description': hour['weatherDesc'][0]['value']
            }

    return {
        'location': location,
        'current': current_snapshot,
        'forecast': forecast
    }


@function_tool
def get_weather(location: str = "Syracuse, NY") -> dict:
    """Get current weather and today's 3-hour forecast for a place.
    Returns temperature, feels-like, conditions, humidity, wind, UV index,
    today's min/max, and chance of rain by time of day. Accepts a city name,
    zip code, airport code (e.g. 'SYR'), or landmark. Defaults to Syracuse, NY."""
    return get_current_weather(location)



weather_agent = Agent(
    name="Weather agent",
    instructions=(
        "Call get_weather for the requested location. If no location is "
        "given, use Syracuse, NY. Summarize the facts that matter (current "
        "conditions, feels-like, high/low, rain chances, wind, UV, and how "
        "the day changes). Do NOT give clothing or activity advice."
    ),
    tools=[get_weather],
    model=MODEL,
)

stylist_agent = Agent(
    name="Stylist agent",
    instructions=(
        "You receive a weather summary. Recommend what to wear today: layers, "
        "footwear, and accessories (umbrella, sunscreen, hat). Account for "
        "temperature changes through the day. Be concise."
    ),
    model=MODEL,
)

activity_agent = Agent(
    name="Activity agent",
    instructions=(
        "You receive a weather summary. Suggest 3 outdoor activities that "
        "suit it, and say what time of day is best. If the weather is poor, "
        "say so honestly and suggest a backup. Be concise."
    ),
    model=MODEL,
)

manager_agent = Agent(
    name="Manager",
    instructions=(
        "You coordinate a team. First call weather_report for the location. "
        "Then pass the weather summary to clothing_advice and activity_advice. "
        "Combine both into one friendly answer with a 'What to wear' section "
        "and an 'What to do' section. If the location can't be found, say so "
        "and ask for a real place instead of guessing."
    ),
    tools=[
        weather_agent.as_tool(
            tool_name="weather_report",
            tool_description="Look up and summarize today's weather for a location.",
        ),
        stylist_agent.as_tool(
            tool_name="clothing_advice",
            tool_description="Given a weather summary, recommend what to wear.",
        ),
        activity_agent.as_tool(
            tool_name="activity_advice",
            tool_description="Given a weather summary, suggest outdoor activities.",
        ),
    ],
    model=MODEL,
)

single_agent = Agent(
    name="Single agent",
    instructions=(
        "You are a 'What to Wear' bot. Call get_weather for the location "
        "(default Syracuse, NY). Then recommend what to wear today, accounting "
        "for changes through the day, and suggest 3 suitable outdoor "
        "activities. If the location can't be found, say so."
    ),
    tools=[get_weather],
    model=MODEL,
)


@st.cache_resource
def get_event_loop():
    return asyncio.new_event_loop()


def run(agent, prompt):
    start = time.perf_counter()
    result = get_event_loop().run_until_complete(Runner.run(agent, prompt))
    return result, time.perf_counter() - start


mode = st.radio("Who answers?", ["Team (manager + specialists)", "Single agent"])
location = st.text_input("City", value="Syracuse, NY")

if st.button("Get advice"):
    agent = manager_agent if mode.startswith("Team") else single_agent
    with st.spinner("Working (the team can take 20-40 seconds)..."):
        result, seconds = run(
            agent, f"What should I wear and do today in {location}?"
        )

    with st.chat_message("assistant"):
        st.write(result.final_output)

    usage = result.context_wrapper.usage
    with st.expander("Behind the scenes"):
        st.write(
            f"Model requests: {usage.requests} · Tokens: {usage.total_tokens:,} · "
            f"Time: {seconds:.1f}s · Answered by: {result.last_agent.name}"
        )
        for item in result.new_items:
            if item.type == "tool_call_item":
                st.write(
                    f"{item.agent.name} called {item.raw_item.name}: "
                    f"{item.raw_item.arguments}"
                )
            elif item.type == "tool_call_output_item":
                st.write(f"result: {str(item.output)[:300]}")
            elif item.type == "handoff_output_item":
                st.write(
                    f"handoff: {item.source_agent.name} -> {item.target_agent.name}"
                )

# Part D answers
# a. Tools the manager called, in order:
# b. What the manager sent the stylist, and who wrote it:
# c. Where the extra model requests came from: