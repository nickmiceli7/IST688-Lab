import streamlit as st
from openai import OpenAI
import requests
import json

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

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather_data",
            "description": "this tool returns information about the weather throughout the day for a given location. input can be a city, zipcode, airport code, or landmark",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Can be a city, zipcode, airport code, or landmark"
                    }
                },
                "required": []
            }
        }
    }
]

if 'open_ai_client' not in st.session_state:
    api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.open_ai_client = OpenAI(api_key=api_key)

system_prompt = {'role': 'system', 'content': "You are a helpful assistant who provides recommendations on what to wear based on the weather."
" If the user doesn't provide a location, default to Syracuse, NY"
}
location = st.text_input("Location:")

messages = []
messages.append(system_prompt)
messages.append({'role': 'user', 'content': f"What should I wear in {location}?"})

if st.button("Get advice"):
    response = st.session_state.open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    response_message = response.choices[0].message

    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        id = tool_call.id
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        location = function_args.get('location') or 'Syracuse, NY' #claude helped with the or statement

        messages.append(response_message.to_dict()) #claude helped with this line

        weather = get_weather_data(location)
        results = json.dumps(weather)

        messages.append({
            "role":"tool",
            "tool_call_id":id,
            "name": function_name,
            "content":results
        })


        stream = st.session_state.open_ai_client.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            stream=True)

        with st.chat_message('assistant'):
                response = st.write_stream(stream)

    else:
        final_answer = response_message.content
        with st.chat_message('assistant'):
                response = st.write(final_answer)