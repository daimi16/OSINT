import requests
import pandas as pd
import json
import os
from datetime import datetime

class GovernmentDataClient:
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.data.gov/"
    
    def get_fda_food_recalls(self, limit=25, skip=0):
        try:
            url = "https://api.fda.gov/food/enforcement.json"
            params = {
                'limit': limit,
                'skip': skip,
                'sort': 'recall_initiation_date:desc'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if 'results' not in data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data['results'])
            return df
        
        except Exception as e:
            print(f"Error fetching FDA food recalls: {e}")
            return pd.DataFrame()
    
    def get_census_population_data(self, year=2019, state=None):
        try:
            url = "https://api.census.gov/data/2019/pep/population"
            
            params = {
                'get': 'NAME,POP',
                'for': 'state:*' if state is None else f'state:{state}'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            headers = data[0]
            rows = data[1:]
            
            df = pd.DataFrame(rows, columns=headers)
            return df
        
        except Exception as e:
            print(f"Error fetching Census population data: {e}")
            return pd.DataFrame()
    
    def get_crime_data_by_city(self, city):
        try:
            city_to_state = {
                'new york': 'NY',
                'los angeles': 'CA',
                'chicago': 'IL',
                'houston': 'TX',
                'phoenix': 'AZ',
                'philadelphia': 'PA',
                'san antonio': 'TX',
                'san diego': 'CA',
                'dallas': 'TX',
                'san jose': 'CA',
                'austin': 'TX',
                'jacksonville': 'FL',
                'fort worth': 'TX',
                'columbus': 'OH',
                'charlotte': 'NC',
                'san francisco': 'CA',
                'indianapolis': 'IN',
                'seattle': 'WA',
                'denver': 'CO',
                'washington': 'DC',
                'boston': 'MA',
                'el paso': 'TX',
                'nashville': 'TN',
                'detroit': 'MI',
                'portland': 'OR',
                'las vegas': 'NV',
                'oklahoma city': 'OK',
                'memphis': 'TN',
                'louisville': 'KY',
                'baltimore': 'MD',
                'miami': 'FL',
                'atlanta': 'GA'
            }
            
            normalized_city = city.lower()
            
            if normalized_city not in city_to_state:
                print(f"City {city} not found in our mapping. Data unavailable.")
                return pd.DataFrame()
            
            state = city_to_state[normalized_city]
            
            base_url = "https://api.usa.gov/crime/fbi/sapi"
            
            agency_url = f"{base_url}/api/agencies/byStateAbbr/{state}"
            
            api_key = 'SZoaqJN6HT0cUb6G04TOAqWVJPUXmrgc7NkJtjOT'
            params = {
                'api_key': api_key
            }
            
            print(f"Agency API URL: {agency_url}")
            print(f"Agency API params: {params}")
            
            try:
                response = requests.get(agency_url, params=params, timeout=10)
                
                if not response.ok and response.status_code == 403:
                    alt_url = f"{agency_url}?api_key={api_key}"
                    print(f"Trying alternative URL approach: {alt_url}")
                    response = requests.get(alt_url, timeout=10)
                
                print(f"Agency API response status: {response.status_code}")
                if not response.ok:
                    print(f"Agency API response text: {response.text[:200]}")
                    if response.status_code == 403:
                        print(f"Authentication error (403) when fetching data for {city}. The API key may be invalid or rate-limited.")
                        return pd.DataFrame()
                    else:
                        print(f"Error fetching agency data for {city}: HTTP {response.status_code} - {response.reason}")
                        return pd.DataFrame()
            
            except Exception as e:
                print(f"Exception making agency request: {e}")
                return pd.DataFrame()
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                print(f"Error decoding JSON response for {city}. Response content: {response.text[:100]}...")
                return pd.DataFrame()
            
            if not data:
                print(f"No agency data found for {city}")
                return pd.DataFrame()
            
            ori = None
            for agency in data:
                agency_name = agency.get('agency_name', '').lower()
                if (normalized_city in agency_name and 
                    ('police' in agency_name or 
                     'county' in agency_name or 
                     'sheriff' in agency_name or
                     'department' in agency_name)):
                    ori = agency.get('ori')
                    print(f"Found matching agency: {agency.get('agency_name')} with ORI: {ori}")
                    break
            
            if not ori:
                for agency in data:
                    agency_name = agency.get('agency_name', '').lower()
                    if normalized_city in agency_name:
                        ori = agency.get('ori')
                        print(f"Found partial match agency: {agency.get('agency_name')} with ORI: {ori}")
                        break
            
            if not ori:
                print(f"Could not find ORI for {city}")
                return pd.DataFrame()
            
            crime_url = f"{base_url}/api/summarized/agencies/{ori}/offenses/2016/2022"
            crime_params = {
                'api_key': api_key
            }
            
            print(f"Crime API URL: {crime_url}")
            print(f"Crime API params: {crime_params}")
            
            try:
                crime_response = requests.get(crime_url, params=crime_params, timeout=10)
                
                if not crime_response.ok and crime_response.status_code == 403:
                    current_year = datetime.now().year
                    alt_crime_url = f"{crime_url}?api_key={api_key}&from=2016&to={str(min(current_year - 1, 2022))}&type=count"
                    print(f"Trying alternative crime URL approach: {alt_crime_url}")
                    crime_response = requests.get(alt_crime_url, timeout=10)
                
                print(f"Crime API response status: {crime_response.status_code}")
                if not crime_response.ok:
                    print(f"Crime API response text: {crime_response.text[:200]}")
                    if crime_response.status_code == 403:
                        print(f"Authentication error (403) when fetching crime data for {city}. The API key may be invalid or rate-limited.")
                        return pd.DataFrame()
                    else:
                        print(f"Error fetching crime data for {city}: HTTP {crime_response.status_code} - {crime_response.reason}")
                        return pd.DataFrame()
                
                try:
                    crime_data = crime_response.json()
                except json.JSONDecodeError:
                    print(f"Error decoding JSON response for crime data in {city}. Response content: {crime_response.text[:100]}...")
                    return pd.DataFrame()
                
                if 'results' not in crime_data:
                    print(f"No crime data found for {city}")
                    return pd.DataFrame()
                    
                crime_df = pd.DataFrame(crime_data['results'])
                
                crime_df['city'] = city
                
                return crime_df
            
            except requests.exceptions.Timeout:
                print(f"Request timed out when fetching crime data for {city}")
                return pd.DataFrame()
            except requests.exceptions.RequestException as e:
                print(f"Request exception when fetching crime data for {city}: {e}")
                return pd.DataFrame()
                
        except requests.exceptions.Timeout:
            print(f"Request timed out when fetching agency data for {city}")
            return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            print(f"Request exception when fetching agency data for {city}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching crime data for {city}: {e}")
            return pd.DataFrame()

    def search_fda_food_recalls(self, search_term, max_results=100):
        try:
            search_term = search_term.strip()
            search_term_lower = search_term.lower()
            
            print(f"Searching for FDA recalls containing: '{search_term}'")
            
            all_results = []
            total_to_search = 10000
            batch_size = 1000
            
            for skip in range(0, total_to_search, batch_size):
                try:
                    print(f"Fetching recalls batch {skip//batch_size + 1} (records {skip} to {skip + batch_size})...")
                    
                    url = "https://api.fda.gov/food/enforcement.json"
                    params = {
                        'limit': batch_size,
                        'skip': skip,
                        'sort': 'recall_initiation_date:desc'
                    }
                    
                    response = requests.get(url, params=params, timeout=15)
                    
                    if response.ok and 'results' in response.json():
                        batch_results = response.json()['results']
                        all_results.extend(batch_results)
                        print(f"Retrieved {len(batch_results)} recalls in batch {skip//batch_size + 1}")
                        
                        if len(batch_results) < batch_size:
                            print(f"Reached end of available recall data after {len(all_results)} total records")
                            break
                    else:
                        print(f"Error fetching batch {skip//batch_size + 1}: {response.status_code}")
                        if skip > 0:
                            break
                        else:
                            print("Failed to retrieve any recall data. FDA API may be unavailable.")
                            return pd.DataFrame()
                
                except Exception as e:
                    print(f"Error in batch {skip//batch_size + 1}: {e}")
                    break
            
            print(f"Retrieved total of {len(all_results)} recalls for local searching")
            
            if not all_results:
                print("No FDA recall data available")
                return pd.DataFrame()
            
            print(f"Searching locally for '{search_term}'...")
            matching_results = []
            
            search_fields = ['product_description', 'reason_for_recall', 'recalling_firm', 
                             'classification', 'code_info', 'product_quantity']
            
            for result in all_results:
                found = False
                
                for field in search_fields:
                    if field in result and search_term_lower in str(result[field]).lower():
                        matching_results.append(result)
                        found = True
                        break
            
            print(f"Found {len(matching_results)} exact matches")
            
            if len(matching_results) < max_results and ' ' in search_term_lower:
                words = search_term_lower.split()
                print(f"Trying word-based search with: {words}")
                
                for result in all_results:
                    if result in matching_results:
                        continue
                    
                    word_matches = 0
                    for field in search_fields:
                        if field in result:
                            field_text = str(result[field]).lower()
                            for word in words:
                                if word in field_text:
                                    word_matches += 1
                    
                    if word_matches > 0:
                        result['_match_score'] = word_matches
                        matching_results.append(result)
                
                seen = set()
                unique_results = []
                for result in matching_results:
                    if 'id' in result:
                        identifier = result['id']
                    else:
                        identifier = f"{result.get('product_description', '')}_{result.get('recall_initiation_date', '')}"
                    
                    if identifier not in seen:
                        seen.add(identifier)
                        unique_results.append(result)
                
                matching_results = unique_results
                
                matching_results.sort(key=lambda x: x.get('_match_score', 0), reverse=True)
                
                print(f"Found {len(matching_results)} matches after word-based search")
            
            if len(matching_results) < max_results:
                print("Trying substring matching...")
                for result in all_results:
                    if result in matching_results:
                        continue
                    
                    for field in search_fields:
                        if field in result:
                            field_text = str(result[field]).lower()
                            
                            if len(search_term_lower) > 3 and any(search_term_lower[i:i+4] in field_text for i in range(len(search_term_lower) - 3)):
                                matching_results.append(result)
                                break
                
                seen = set()
                unique_results = []
                for result in matching_results:
                    if 'id' in result:
                        identifier = result['id']
                    else:
                        identifier = f"{result.get('product_description', '')}_{result.get('recall_initiation_date', '')}"
                    
                    if identifier not in seen:
                        seen.add(identifier)
                        unique_results.append(result)
                
                matching_results = unique_results
                print(f"Found {len(matching_results)} matches after substring matching")
            
            if matching_results:
                for result in matching_results:
                    if '_match_score' in result:
                        del result['_match_score']
                
                result_df = pd.DataFrame(matching_results[:max_results])
                print(f"Returning {len(result_df)} FDA recall results")
                return result_df
            
            print("No matching FDA recall results found")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Error searching FDA food recalls: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

if __name__ == "__main__":
    client = GovernmentDataClient()
    
    crime_data = client.get_crime_data_by_city("Chicago")
    print(crime_data.head()) 