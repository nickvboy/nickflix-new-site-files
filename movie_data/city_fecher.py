import json
import os
import csv
import time
import requests
import zipfile
import io

def main():
    # Log start time
    start_time = time.time()
    print("Starting US populated places data extraction...")
    
    # Output file path - save directly in movie_data folder
    output_file = os.path.join(os.path.dirname(__file__), "us_cities.json")
    print(f"Output will be saved to: {output_file}")
    
    # Dictionary to store places data
    all_places = {}
    
    # Flag to track if we successfully loaded data
    data_loaded = False
    
    # Step 1: Get geographical data from Census Bureau Gazetteer Files
    census_places_url = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_place_national.zip"
    
    print(f"Downloading Census Bureau Places Gazetteer File for geographic data from {census_places_url}...")
    
    try:
        # Download the Census Bureau Places Gazetteer File
        response = requests.get(census_places_url, stream=True)
        response.raise_for_status()
        
        # Extract the zip file in memory
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            # Get the name of the text file (typically 2024_Gaz_place_national.txt)
            txt_file = [name for name in zip_ref.namelist() if name.endswith('.txt')][0]
            
            print(f"Processing file: {txt_file}")
            
            # Extract and process the file
            with zip_ref.open(txt_file) as f:
                # Convert bytes to string
                content = io.TextIOWrapper(f, encoding='utf-8')
                
                # Create a CSV reader with tab delimiter
                csv_reader = csv.reader(content, delimiter='\t')
                
                # Get header (first row)
                header_raw = next(csv_reader)
                
                # Clean up header - strip whitespace from each column name
                header = [col.strip() for col in header_raw]
                print(f"Found header (cleaned): {header}")
                
                # Try to find indices based on common names for these fields
                name_idx = None
                state_idx = None
                lat_idx = None
                lon_idx = None
                geoid_idx = None
                land_area_idx = None
                water_area_idx = None
                
                for i, col in enumerate(header):
                    if col == 'NAME':
                        name_idx = i
                    elif col == 'USPS':
                        state_idx = i
                    elif col in ['INTPTLAT', 'INTPTLAT_CURRENT']:
                        lat_idx = i
                    elif col in ['INTPTLONG', 'INTPTLONG_CURRENT', 'INTPTLON', 'INTPTLON_CURRENT']:
                        lon_idx = i
                    elif col == 'GEOID':
                        geoid_idx = i
                    elif col in ['ALAND_SQMI', 'LAND_SQMI']:
                        land_area_idx = i
                    elif col in ['AWATER_SQMI', 'WATER_SQMI']:
                        water_area_idx = i
                
                # Check if we found all the needed indices
                if None in [name_idx, state_idx, lat_idx, lon_idx]:
                    raise ValueError(f"Could not find all required columns in the header: {header}")
                
                print(f"Using columns - Name: {header[name_idx]}, State: {header[state_idx]}, " +
                      f"Latitude: {header[lat_idx]}, Longitude: {header[lon_idx]}")
                
                # Process all places
                place_count = 0
                
                print("Processing cities and places from Census Bureau Gazetteer data...")
                
                for row in csv_reader:
                    # Check if row has enough elements
                    required_max_idx = max(idx for idx in [name_idx, state_idx, lat_idx, lon_idx] if idx is not None)
                    if len(row) <= required_max_idx:
                        continue
                    
                    try:
                        # Create place object
                        place = {
                            'name': row[name_idx].strip(),
                            'state': row[state_idx].strip(),
                            'latitude': float(row[lat_idx].strip()),
                            'longitude': float(row[lon_idx].strip()),
                        }
                        
                        # Add optional fields if available
                        if geoid_idx is not None and geoid_idx < len(row):
                            place['geoid'] = row[geoid_idx].strip()
                        if land_area_idx is not None and land_area_idx < len(row) and row[land_area_idx].strip():
                            try:
                                place['land_area_sqmi'] = float(row[land_area_idx].strip())
                            except ValueError:
                                pass
                        if water_area_idx is not None and water_area_idx < len(row) and row[water_area_idx].strip():
                            try:
                                place['water_area_sqmi'] = float(row[water_area_idx].strip())
                            except ValueError:
                                pass
                        
                        # Use GEOID as key if available, otherwise use name_state combination
                        if 'geoid' in place:
                            key = place['geoid']
                        else:
                            # Create a key from name and state
                            key = f"{place['name']}_{place['state']}".replace(' ', '_')
                        
                        # Add to dictionary using the key
                        all_places[key] = place
                        place_count += 1
                        
                        # Log progress periodically
                        if place_count % 1000 == 0:
                            print(f"Processed {place_count} places so far...")
                        
                        # Log each place found (but limit console output)
                        if place_count <= 10:
                            print(f"Found place: {place['name']}, {place['state']}")
                        elif place_count == 11:
                            print("... (output truncated to avoid overwhelming console) ...")
                    except (ValueError, IndexError) as e:
                        print(f"Error processing row {row}: {e}")
                        continue
                
                print(f"Successfully loaded geographic data for {place_count} places")
                data_loaded = True
        
        # Step 2: Get population data from Census Bureau Population Estimates
        census_pop_url = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/cities/totals/sub-est2023.csv"
        
        print(f"\nDownloading Census Bureau Population Estimates from {census_pop_url}...")
        
        try:
            response = requests.get(census_pop_url)
            response.raise_for_status()
            
            # Process the CSV file
            content = response.text.splitlines()
            reader = csv.reader(content)
            header = next(reader)
            print(f"Found population data header: {header}")
            
            # Create dictionaries for city name/state normalization
            state_abbrevs = {
                "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
                "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
                "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
                "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
                "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
                "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
                "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
                "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
                "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
                "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
                "District of Columbia": "DC", "Puerto Rico": "PR"
            }
            
            # Find indices for needed fields
            try:
                name_idx = header.index('NAME')
                state_idx = header.index('STNAME')
                place_idx = header.index('PLACE')
                pop_idx = header.index('POPESTIMATE2023')
                sumlev_idx = header.index('SUMLEV')
                
                print(f"Using population data columns - Name: {header[name_idx]}, State: {header[state_idx]}, " +
                      f"Place Code: {header[place_idx]}, Population 2023: {header[pop_idx]}")
            except ValueError:
                # If column names are different, try to find similar ones
                name_idx = next((i for i, col in enumerate(header) if 'NAME' in col), None)
                state_idx = next((i for i, col in enumerate(header) if 'STNAME' in col or 'STATE' in col), None)
                place_idx = next((i for i, col in enumerate(header) if 'PLACE' in col), None)
                pop_idx = next((i for i, col in enumerate(header) if 'POP' in col and '2023' in col), None)
                sumlev_idx = next((i for i, col in enumerate(header) if 'SUMLEV' in col), None)
                
                if None in [name_idx, state_idx, place_idx, pop_idx, sumlev_idx]:
                    raise ValueError(f"Could not find all required population columns in the header: {header}")
                
                print(f"Using similar population columns - Name: {header[name_idx]}, State: {header[state_idx]}, " +
                      f"Place Code: {header[place_idx]}, Population: {header[pop_idx]}")
            
            print("\nMerging population data with geographic data...")
            pop_added_count = 0
            new_places_count = 0
            
            # Dictionary to store population data by normalized name_state key
            pop_data = {}
            
            # First pass: collect all population data
            print("First pass: collecting population data...")
            for row in reader:
                # Make sure the row has enough elements
                if len(row) <= max(name_idx, state_idx, place_idx, pop_idx, sumlev_idx):
                    continue
                
                # Check for places (SUMLEV code 160 or 162 for incorporated places)
                # A SUMLEV of 160 represents "Place" and 162 represents "Incorporated Place"
                if row[sumlev_idx] in ['160', '162', '170']:
                    try:
                        # Get population value
                        population = None
                        if row[pop_idx].strip():
                            try:
                                # Try parsing as integer
                                population = int(row[pop_idx].strip())
                            except ValueError:
                                # Try removing commas and parsing
                                try:
                                    population = int(row[pop_idx].strip().replace(',', ''))
                                except ValueError:
                                    pass
                        
                        # Skip if no valid population
                        if population is None:
                            continue
                        
                        # Get place name and state
                        place_name = row[name_idx].strip()
                        state_name = row[state_idx].strip()
                        state_abbr = state_abbrevs.get(state_name, state_name)  # Convert full state name to abbreviation
                        place_code = row[place_idx].strip() if place_idx < len(row) else ""
                        
                        # Create normalized keys for matching
                        name_state_key = f"{place_name}_{state_name}".replace(' ', '_').lower()
                        name_abbr_key = f"{place_name}_{state_abbr}".replace(' ', '_').lower()
                        
                        # Store data with all possible keys
                        pop_data[name_state_key] = {
                            'name': place_name,
                            'state': state_abbr,
                            'population': population,
                            'place_code': place_code
                        }
                        
                        if name_state_key != name_abbr_key:
                            pop_data[name_abbr_key] = pop_data[name_state_key]
                        
                        # Also store by place code
                        if place_code:
                            pop_data[place_code] = pop_data[name_state_key]
                        
                    except Exception as e:
                        print(f"Error processing population row: {e}")
                        continue
            
            print(f"Collected population data for {len(pop_data)} unique places")
            
            # Second pass: match and merge with geographic data
            print("Second pass: merging population data with geographic data...")
            
            # First try to add population to existing geographic entries
            for key, place in all_places.items():
                try:
                    # Try different keys for matching
                    name_state_key = f"{place['name']}_{place['state']}".replace(' ', '_').lower()
                    
                    # Try to find a match in population data
                    if name_state_key in pop_data:
                        place['population'] = pop_data[name_state_key]['population']
                        pop_added_count += 1
                        # Remove from pop_data to track what's been matched
                        pop_data.pop(name_state_key, None)
                    elif key in pop_data:
                        place['population'] = pop_data[key]['population']
                        pop_added_count += 1
                        pop_data.pop(key, None)
                    elif place.get('geoid') and place['geoid'] in pop_data:
                        place['population'] = pop_data[place['geoid']]['population']
                        pop_added_count += 1
                        pop_data.pop(place['geoid'], None)
                except Exception as e:
                    print(f"Error matching population for {place.get('name')}: {e}")
            
            # Add remaining population entries as new places
            for key, pop_place in pop_data.items():
                if key.isdigit() or '_' not in key:  # Skip duplicated keys (place codes or non-combined keys)
                    continue
                    
                # Only add this entry if we don't already have a similar one
                name_parts = pop_place['name'].lower().split()
                state_abbr = pop_place['state']
                
                # Check if we already have this city with a slightly different name
                duplicate = False
                for existing_key, existing_place in all_places.items():
                    if existing_place.get('state') == state_abbr:
                        existing_name_parts = existing_place.get('name', '').lower().split()
                        # Check if first parts of names match (e.g., "New York" vs "New York city")
                        if len(name_parts) > 0 and len(existing_name_parts) > 0:
                            if name_parts[0] == existing_name_parts[0]:
                                duplicate = True
                                break
                
                if not duplicate:
                    # Create a normalized key
                    new_key = f"{pop_place['name']}_{pop_place['state']}".replace(' ', '_')
                    
                    # Create a new place entry with population data
                    new_place = {
                        'name': pop_place['name'],
                        'state': pop_place['state'],
                        'population': pop_place['population']
                    }
                    
                    # Add to our collection
                    all_places[new_key] = new_place
                    new_places_count += 1
            
            print(f"Added population data to {pop_added_count} existing places")
            print(f"Added {new_places_count} new places with population data")
            
            # Check for major cities to make sure they have population data
            major_cities = ["New York city", "Los Angeles city", "Chicago city", "Houston city", "Phoenix city"]
            print("\nVerifying population data for major cities:")
            for city_name in major_cities:
                found = False
                for key, place in all_places.items():
                    if place['name'] == city_name:
                        found = True
                        has_pop = 'population' in place
                        pop_value = place.get('population', 'N/A')
                        print(f"  {city_name}, {place['state']}: Has population: {has_pop}, Value: {pop_value}")
                        if not has_pop:
                            # Try to fix missing population for major cities
                            for pop_key, pop_data_entry in pop_data.items():
                                if city_name.lower() in pop_key.lower():
                                    place['population'] = pop_data_entry['population']
                                    print(f"    FIXED: Added population {pop_data_entry['population']} to {city_name}")
                                    break
                
                if not found:
                    print(f"  WARNING: {city_name} not found in dataset")
            
        except Exception as e:
            print(f"Error with Census Bureau Population Estimates: {e}")
            print("Continuing with geographic data only (no population)")
        
        # Save to JSON file with explicit encoding
        print(f"\nWriting {len(all_places)} places to {output_file}...")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_places, f, ensure_ascii=False, indent=2)
            
            # Verify saved file
            print("Verifying saved JSON file...")
            with open(output_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                
            # Check sample of data
            print(f"Successfully loaded JSON file with {len(loaded_data)} entries")
            
            # Check for population data in loaded file
            places_with_pop = sum(1 for place in loaded_data.values() if 'population' in place)
            print(f"Places with population data in saved file: {places_with_pop}")
            
            # Print statistics
            places_with_pop = sum(1 for place in all_places.values() if 'population' in place)
            print(f"Places with population data: {places_with_pop} out of {len(all_places)} total places")
            print(f"Percentage with population: {places_with_pop/len(all_places)*100:.1f}%")
            
        except Exception as e:
            print(f"Error saving JSON file: {e}")
        
        elapsed_time = time.time() - start_time
        print(f"Process completed in {elapsed_time:.2f} seconds")
        
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error with Census Bureau Gazetteer File: {e}")
        
        # Fallback to geonamescache if we didn't load any data
        if not data_loaded:
            print("Census Bureau sources failed. Falling back to geonamescache...")
            try:
                from geonamescache import GeonamesCache
                
                # Create a GeonamesCache instance
                gc = GeonamesCache()
                
                # Get all cities
                print("Fetching cities from geonamescache...")
                total_cities = gc.get_cities()
                print(f"Total cities in cache: {len(total_cities)}")
                
                # Filter US cities
                us_cities = [city for city in total_cities.values() if city['countrycode'] == 'US']
                
                # Create a flat dictionary
                filtered_places = {}
                
                for city in us_cities:
                    # Create a copy without alternatenames
                    filtered_city = {k: v for k, v in city.items() if k != 'alternatenames'}
                    
                    # Explicitly include population
                    if 'population' in city:
                        filtered_city['population'] = city['population']
                    
                    # Use geonameid as key
                    key = str(filtered_city.get('geonameid', f"{filtered_city['name']}_{filtered_city.get('admin1code', 'Unknown')}"))
                    
                    # Add to dictionary
                    filtered_places[key] = filtered_city
                    
                    # Log each city found (limit output)
                    if len(filtered_places) <= 10:
                        pop_str = f", Population: {filtered_city.get('population', 'N/A')}"
                        print(f"Found city: {filtered_city['name']}, {filtered_city.get('admin1code', 'Unknown State')}{pop_str}")
                    elif len(filtered_places) == 11:
                        print("... (output truncated to avoid overwhelming console) ...")
                
                # Save to JSON file
                print(f"Writing {len(filtered_places)} cities to {output_file}...")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(filtered_places, f, indent=2)
                
                elapsed_time = time.time() - start_time
                print(f"Process completed in {elapsed_time:.2f} seconds")
                print(f"Found {len(us_cities)} cities in the US (limited set from geonamescache)")
                print(f"Data saved to {output_file}")
                
            except ImportError:
                print("Geonamescache not installed. Please install with: pip install geonamescache")
                print("No data sources were available to create the US cities database.")

if __name__ == "__main__":
    main()