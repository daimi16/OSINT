import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta

class FlightDataClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.aviationstack.com/v1/"
    
    def get_real_time_flights(self, limit=100, offset=0, flight_status=None, airline_iata=None, departure_city=None):
        try:
            print(f"Starting get_real_time_flights with params: status={flight_status}, city={departure_city}, limit={limit}")
            url = f"{self.base_url}flights"
            
            params = {
                'access_key': self.api_key,
                'limit': limit,
                'offset': offset
            }
            
            if flight_status:
                params['flight_status'] = flight_status
            if airline_iata:
                params['airline_iata'] = airline_iata
            if departure_city:
                dep_iata = self.get_airport_iata_by_city(departure_city)
                if dep_iata:
                    params['dep_iata'] = dep_iata
                    print(f"Using departure airport IATA code: {dep_iata}")
                else:
                    print(f"Could not find IATA code for city: {departure_city}")
            
            print(f"API Request URL: {url}")
            print(f"API Request Params: {params}")
            response = requests.get(url, params=params)
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 429:
                print("API USAGE ERROR: Monthly usage limit has been reached")
                raise Exception("Monthly API usage limit reached (100 calls for free tier)")
                
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                error_code = data.get('error', {}).get('code', '')
                error_msg = data.get('error', {}).get('message', '')
                print(f"API Error: {error_code} - {error_msg}")
                
                if 'usage_limit_reached' in error_code:
                    raise Exception("Monthly API usage limit reached (100 calls for free tier)")
                elif 'invalid_access_key' in error_code:
                    raise Exception("Invalid API access key. Please check your key in config.py")
                elif 'inactive_user' in error_code:
                    raise Exception("Inactive user account. Please activate your account on the AviationStack website")
                else:
                    raise Exception(f"API Error: {error_msg}")
            
            print(f"API Response Keys: {data.keys() if data else 'No data'}")
            
            if 'data' not in data or not data['data']:
                print("No flight data in response")
                return pd.DataFrame()
            
            print(f"Found {len(data['data'])} flights in response")
            flattened_data = []
            for flight in data['data']:
                flight_info = {}
                
                flight_info['flight_date'] = flight.get('flight_date')
                flight_info['flight_status'] = flight.get('flight_status')
                
                if 'flight' in flight:
                    flight_info['flight_number'] = flight['flight'].get('number')
                    flight_info['flight_iata'] = flight['flight'].get('iata')
                    flight_info['flight_icao'] = flight['flight'].get('icao')
                
                if 'airline' in flight:
                    flight_info['airline_name'] = flight['airline'].get('name')
                    flight_info['airline_iata'] = flight['airline'].get('iata')
                    flight_info['airline_icao'] = flight['airline'].get('icao')
                
                if 'departure' in flight:
                    departure_data = flight['departure']
                    for key, value in departure_data.items():
                        flight_info[f'departure_{key}'] = value
                
                if 'arrival' in flight:
                    arrival_data = flight['arrival']
                    for key, value in arrival_data.items():
                        flight_info[f'arrival_{key}'] = value
                
                have_coordinates = (
                    'departure_latitude' in flight_info and 
                    'departure_longitude' in flight_info and
                    'arrival_latitude' in flight_info and 
                    'arrival_longitude' in flight_info
                )
                
                if have_coordinates:
                    print(f"Flight {flight_info.get('flight_iata', 'Unknown')}: "
                          f"From {flight_info.get('departure_airport', 'Unknown')} "
                          f"({flight_info.get('departure_latitude', '?')}, {flight_info.get('departure_longitude', '?')}) "
                          f"To {flight_info.get('arrival_airport', 'Unknown')} "
                          f"({flight_info.get('arrival_latitude', '?')}, {flight_info.get('arrival_longitude', '?')})")
                          
                flattened_data.append(flight_info)
            
            df = pd.DataFrame(flattened_data)
            return df
        
        except Exception as e:
            print(f"Error fetching real-time flights: {e}")
            return pd.DataFrame()
    
    def get_airport_data(self, iata_code=None, country=None, limit=100, offset=0):
        try:
            url = f"{self.base_url}airports"
            
            params = {
                'access_key': self.api_key,
                'limit': limit,
                'offset': offset
            }
            
            if iata_code:
                params['iata_code'] = iata_code
            if country:
                params['country_name'] = country
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or not data['data']:
                return pd.DataFrame()
            
            df = pd.DataFrame(data['data'])
            return df
        
        except Exception as e:
            print(f"Error fetching airport data: {e}")
            return pd.DataFrame()
    
    def get_airline_data(self, iata_code=None, country=None, limit=100, offset=0):
        try:
            url = f"{self.base_url}airlines"
            
            params = {
                'access_key': self.api_key,
                'limit': limit,
                'offset': offset
            }
            
            if iata_code:
                params['iata_code'] = iata_code
            if country:
                params['country_name'] = country
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or not data['data']:
                return pd.DataFrame()
            
            df = pd.DataFrame(data['data'])
            return df
        
        except Exception as e:
            print(f"Error fetching airline data: {e}")
            return pd.DataFrame()
    
    def get_historical_flights(self, flight_icao=None, flight_date=None, limit=100, offset=0):
        try:
            url = f"{self.base_url}flights"
            
            params = {
                'access_key': self.api_key,
                'limit': limit,
                'offset': offset
            }
            
            if flight_icao:
                params['flight_icao'] = flight_icao
            
            if not flight_date:
                yesterday = datetime.now() - timedelta(days=1)
                flight_date = yesterday.strftime('%Y-%m-%d')
            
            params['flight_date'] = flight_date
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or not data['data']:
                return pd.DataFrame()
            
            flattened_data = []
            for flight in data['data']:
                flight_info = {}
                
                flight_info['flight_date'] = flight.get('flight_date')
                flight_info['flight_status'] = flight.get('flight_status')
                
                if 'flight' in flight:
                    flight_info['flight_number'] = flight['flight'].get('number')
                    flight_info['flight_iata'] = flight['flight'].get('iata')
                    flight_info['flight_icao'] = flight['flight'].get('icao')
                
                if 'airline' in flight:
                    flight_info['airline_name'] = flight['airline'].get('name')
                    flight_info['airline_iata'] = flight['airline'].get('iata')
                    flight_info['airline_icao'] = flight['airline'].get('icao')
                
                if 'departure' in flight:
                    flight_info['departure_airport'] = flight['departure'].get('airport')
                    flight_info['departure_iata'] = flight['departure'].get('iata')
                    flight_info['departure_icao'] = flight['departure'].get('icao')
                    flight_info['departure_terminal'] = flight['departure'].get('terminal')
                    flight_info['departure_gate'] = flight['departure'].get('gate')
                    flight_info['departure_scheduled'] = flight['departure'].get('scheduled')
                    flight_info['departure_actual'] = flight['departure'].get('actual')
                
                if 'arrival' in flight:
                    flight_info['arrival_airport'] = flight['arrival'].get('airport')
                    flight_info['arrival_iata'] = flight['arrival'].get('iata')
                    flight_info['arrival_icao'] = flight['arrival'].get('icao')
                    flight_info['arrival_terminal'] = flight['arrival'].get('terminal')
                    flight_info['arrival_gate'] = flight['arrival'].get('gate')
                    flight_info['arrival_scheduled'] = flight['arrival'].get('scheduled')
                    flight_info['arrival_actual'] = flight['arrival'].get('actual')
                
                flattened_data.append(flight_info)
            
            df = pd.DataFrame(flattened_data)
            return df
        
        except Exception as e:
            print(f"Error fetching historical flights: {e}")
            return pd.DataFrame()

    def get_airport_iata_by_city(self, city_name):
        common_airports = {
            "Atlanta": "ATL",
            "Boston": "BOS",
            "Chicago": "ORD",
            "Dallas": "DFW",
            "Denver": "DEN",
            "Detroit": "DTW",
            "Houston": "IAH",
            "Las Vegas": "LAS",
            "Los Angeles": "LAX",
            "Miami": "MIA",
            "Minneapolis": "MSP",
            "New York": "JFK",
            "Orlando": "MCO",
            "Philadelphia": "PHL",
            "Phoenix": "PHX",
            "San Diego": "SAN",
            "San Francisco": "SFO",
            "Seattle": "SEA",
            "Washington DC": "IAD",
            "London": "LHR",
            "Paris": "CDG",
            "Tokyo": "HND",
            "Beijing": "PEK",
            "Sydney": "SYD",
            "Dubai": "DXB",
            "Toronto": "YYZ",
            "Mexico City": "MEX",
            "Berlin": "BER",
            "Madrid": "MAD"
        }
        
        if city_name in common_airports:
            iata_code = common_airports[city_name]
            print(f"Using mapped IATA code for {city_name}: {iata_code}")
            return iata_code
            
        try:
            print(f"Looking up IATA code for city: {city_name}")
            if len(city_name) == 3 and city_name.isupper():
                print(f"Input appears to be an IATA code already: {city_name}")
                return city_name
                
            url = f"{self.base_url}airports"
            
            params = {
                'access_key': self.api_key,
                'city_name': city_name,
                'limit': 10
            }
            
            print(f"Making request to: {url} with params: {params}")
            response = requests.get(url, params=params)
            print(f"API Response Status: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
            print(f"API response: {data.keys()}")
            
            if 'data' not in data or not data['data']:
                print(f"No airport found for city: {city_name}")
                return None
            
            airports = data['data']
            print(f"Found {len(airports)} airports for {city_name}")
            
            if airports and 'iata_code' in airports[0]:
                iata_code = airports[0]['iata_code']
                print(f"Using IATA code: {iata_code}")
                return iata_code
            
            print("No IATA code found in response")
            return None
            
        except Exception as e:
            print(f"Error fetching airport data for city {city_name}: {e}")
            return None

    def get_direct_airport_flights(self, dep_iata, limit=100, offset=0, flight_status=None):
        try:
            print(f"DIRECT AIRPORT SEARCH: Using IATA code {dep_iata} directly")
            url = f"{self.base_url}flights"
            
            params = {
                'access_key': self.api_key,
                'limit': limit,
                'offset': offset,
                'dep_iata': dep_iata
            }
            
            if flight_status:
                params['flight_status'] = flight_status
            
            print(f"Direct Airport API Request: {url}")
            print(f"Direct Airport API Params: {params}")
            response = requests.get(url, params=params)
            print(f"Direct Airport API Response Status: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
            print(f"Direct Airport API Response Keys: {data.keys() if data else 'No data'}")
            
            if 'error' in data:
                error_code = data.get('error', {}).get('code', '')
                error_msg = data.get('error', {}).get('message', '')
                print(f"API Error: {error_code} - {error_msg}")
                
                if 'usage_limit_reached' in error_code:
                    raise Exception("Monthly API usage limit reached (100 calls for free tier)")
                elif 'invalid_access_key' in error_code:
                    raise Exception("Invalid API access key. Please check your key in config.py")
                elif 'inactive_user' in error_code:
                    raise Exception("Inactive user account. Please activate your account on the AviationStack website")
                else:
                    raise Exception(f"API Error: {error_msg}")
            
            if 'data' not in data or not data['data']:
                print(f"No flight data found for airport {dep_iata}")
                return pd.DataFrame()
            
            print(f"Found {len(data['data'])} flights for airport {dep_iata}")
            
            flattened_data = []
            for flight in data['data']:
                flight_info = {}
                
                flight_info['flight_date'] = flight.get('flight_date')
                flight_info['flight_status'] = flight.get('flight_status')
                
                if 'flight' in flight:
                    flight_info['flight_number'] = flight['flight'].get('number')
                    flight_info['flight_iata'] = flight['flight'].get('iata')
                    flight_info['flight_icao'] = flight['flight'].get('icao')
                
                if 'airline' in flight:
                    flight_info['airline_name'] = flight['airline'].get('name')
                    flight_info['airline_iata'] = flight['airline'].get('iata')
                    flight_info['airline_icao'] = flight['airline'].get('icao')
                
                if 'departure' in flight:
                    departure_data = flight['departure']
                    for key, value in departure_data.items():
                        flight_info[f'departure_{key}'] = value
                
                if 'arrival' in flight:
                    arrival_data = flight['arrival']
                    for key, value in arrival_data.items():
                        flight_info[f'arrival_{key}'] = value
                
                have_coordinates = (
                    'departure_latitude' in flight_info and 
                    'departure_longitude' in flight_info and
                    'arrival_latitude' in flight_info and 
                    'arrival_longitude' in flight_info
                )
                
                if have_coordinates:
                    print(f"Flight {flight_info.get('flight_iata', 'Unknown')}: "
                          f"From {flight_info.get('departure_airport', 'Unknown')} "
                          f"({flight_info.get('departure_latitude', '?')}, {flight_info.get('departure_longitude', '?')}) "
                          f"To {flight_info.get('arrival_airport', 'Unknown')} "
                          f"({flight_info.get('arrival_latitude', '?')}, {flight_info.get('arrival_longitude', '?')})")
                
                flattened_data.append(flight_info)
            
            df = pd.DataFrame(flattened_data)
            return df
            
        except Exception as e:
            print(f"Error fetching direct airport flights: {e}")
            raise

if __name__ == "__main__":
    API_KEY = "your-aviation-stack-api-key"
    
    client = FlightDataClient(API_KEY)
    
    flights = client.get_real_time_flights(limit=10, flight_status='active')
    print(flights.head())