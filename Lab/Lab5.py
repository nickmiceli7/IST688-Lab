import streamlit as st
from openai import OpenAI
import requests

def get_weather_data(location='Syracyse'):
    url = f'https://wttr.in/{location}?format=j1'
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        raise Exception(f'wttr.in error: status {response.status_code}')
    try:
        data = response.json()
    except ValueError:
        # unknown locations come back as plain text, not JSON
            raise Exception(f'Could not find a location named {location}')
        # j1 has three top-level sections:
        # current_condition -- one entry, conditions right now
        # weather -- three entries, one per day, each with
        # min/max, astronomy, and hourly forecasts
        # nearest_area -- the location wttr.in actually matched
    current = data['current_condition'][0]
    today = data['weather'][0]

    time_labels = {'900': '9am', '1200': '12pm', '1500': '3pm', '1800': '6pm'}

    current_snapshot = {
        'temp_f': float(current['temp_F']),
        'feels_like_f': float(current['FeelsLikeF']),
        'description': current['weatherDesc'][0]['value']
    }

    forecast = {}
    for hour in today['hourly']: #claude helped me nest the if statement into the for loop
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

print(get_weather_data('Syracuse, NY'))
