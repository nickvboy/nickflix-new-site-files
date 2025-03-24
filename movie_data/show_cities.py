#!/usr/bin/env python3
"""
A simple script to display city and theater data from MongoDB without re-importing.
This allows checking what data is already in the database.
"""

import os
import json
import sys
from pymongo import MongoClient
from bson.json_util import dumps
from tabulate import tabulate

# MongoDB Configuration
MONGODB_CONNECTION_STRING = "mongodb://localhost:27017/movie_database"
MONGODB_DATABASE = "movie_database"
MONGODB_COLLECTION_CITIES = "cities"
MONGODB_COLLECTION_THEATERS = "theaters"

def connect_to_mongodb():
    """Connect to MongoDB and return client, db and collections."""
    try:
        # Connect to MongoDB
        print(f"Connecting to MongoDB at {MONGODB_CONNECTION_STRING}...")
        client = MongoClient(MONGODB_CONNECTION_STRING)
        
        # Test connection
        client.admin.command('ping')
        print("MongoDB connection successful!")
        
        # Get database and collections
        db = client[MONGODB_DATABASE]
        cities_collection = db[MONGODB_COLLECTION_CITIES]
        theaters_collection = db[MONGODB_COLLECTION_THEATERS]
        
        return client, db, cities_collection, theaters_collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        sys.exit(1)

def show_city_count(cities_collection):
    """Show the count of cities in the database."""
    total_cities = cities_collection.count_documents({})
    processed_cities = cities_collection.count_documents({"processed": True})
    pending_cities = cities_collection.count_documents({"processed": {"$ne": True}})
    population_cities = cities_collection.count_documents({"population": {"$exists": True, "$ne": None}})
    
    print("\n=== City Statistics ===")
    stats = [
        ["Total cities", total_cities],
        ["Cities processed", processed_cities],
        ["Cities pending", pending_cities],
        ["Cities with population data", population_cities]
    ]
    print(tabulate(stats, headers=["Statistic", "Count"], tablefmt="pretty"))

def show_theater_count(theaters_collection):
    """Show the count of theaters in the database."""
    total_theaters = theaters_collection.count_documents({})
    
    # Count by brand
    pipeline = [
        {"$group": {"_id": "$brand", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    brand_counts = list(theaters_collection.aggregate(pipeline))
    
    print("\n=== Theater Statistics ===")
    print(f"Total theaters: {total_theaters}")
    
    if brand_counts:
        print("\n=== Theaters by Brand ===")
        brand_stats = [[brand["_id"], brand["count"]] for brand in brand_counts]
        print(tabulate(brand_stats, headers=["Brand", "Count"], tablefmt="pretty"))

def show_top_cities(cities_collection, limit=10):
    """Show the top cities by population."""
    cursor = cities_collection.find(
        {"population": {"$exists": True, "$ne": None}},
        {"_id": 0, "name": 1, "state": 1, "population": 1, "processed": 1, "theaters_found": 1}
    ).sort("population", -1).limit(limit)
    
    cities = list(cursor)
    
    print(f"\n=== Top {limit} Cities by Population ===")
    city_data = []
    for city in cities:
        processed = "Yes" if city.get("processed", False) else "No"
        theaters = city.get("theaters_found", 0)
        city_data.append([
            f"{city.get('name')}, {city.get('state')}",
            city.get("population", "N/A"),
            processed,
            theaters
        ])
    
    print(tabulate(city_data, headers=["City", "Population", "Processed", "Theaters Found"], tablefmt="pretty"))

def show_recent_theaters(theaters_collection, limit=10):
    """Show most recently added theaters."""
    cursor = theaters_collection.find(
        {},
        {"_id": 0, "name": 1, "brand": 1, "source_city": 1, "last_updated": 1}
    ).sort("last_updated", -1).limit(limit)
    
    theaters = list(cursor)
    
    print(f"\n=== {limit} Most Recently Added Theaters ===")
    theater_data = []
    for theater in theaters:
        theater_data.append([
            theater.get("name", "Unnamed"),
            theater.get("brand", "Unknown"),
            theater.get("source_city", "Unknown"),
            theater.get("last_updated", "Unknown")
        ])
    
    print(tabulate(theater_data, headers=["Theater Name", "Brand", "City", "Last Updated"], tablefmt="pretty"))

def show_theaters_by_city(theaters_collection, cities_collection, city_name=None):
    """Show theaters for a specific city or sorted by city."""
    if city_name:
        # Find city by name
        city_query = {"name": {"$regex": f"^{city_name}", "$options": "i"}}
        city = cities_collection.find_one(city_query)
        
        if not city:
            print(f"No city found matching '{city_name}'")
            return
        
        # Get theaters for this city
        geoid = city.get("geoid")
        theaters = list(theaters_collection.find({"city_geoid": geoid}))
        
        print(f"\n=== Theaters in {city.get('name')}, {city.get('state')} ===")
        print(f"Found {len(theaters)} theaters")
        
        if theaters:
            theater_data = []
            for theater in theaters:
                theater_data.append([
                    theater.get("name", "Unnamed"),
                    theater.get("brand", "Unknown"),
                    theater.get("address", {}).get("street", "Unknown")
                ])
            
            print(tabulate(theater_data, headers=["Theater Name", "Brand", "Street"], tablefmt="pretty"))
    else:
        # Group theaters by city
        pipeline = [
            {"$group": {"_id": "$source_city", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        city_counts = list(theaters_collection.aggregate(pipeline))
        
        print("\n=== Top 20 Cities by Theater Count ===")
        city_stats = [[city["_id"], city["count"]] for city in city_counts]
        print(tabulate(city_stats, headers=["City", "Theater Count"], tablefmt="pretty"))

def export_cities_json(cities_collection, filename="cities_export.json", limit=100):
    """Export cities to a JSON file."""
    cursor = cities_collection.find(
        {"theaters_found": {"$gt": 0}},
        {"_id": 0}
    ).sort("population", -1).limit(limit)
    
    cities = list(cursor)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(dumps(cities, indent=2))
    
    print(f"\nExported {len(cities)} cities with theaters to {filename}")

def export_theaters_json(theaters_collection, filename="theaters_export.json", limit=None):
    """Export theaters to a JSON file."""
    query = {}
    projection = {"_id": 0}
    
    if limit:
        cursor = theaters_collection.find(query, projection).limit(limit)
    else:
        cursor = theaters_collection.find(query, projection)
    
    theaters = list(cursor)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(dumps(theaters, indent=2))
    
    print(f"\nExported {len(theaters)} theaters to {filename}")

def main():
    """Main function to show MongoDB data."""
    # Connect to MongoDB
    client, db, cities_collection, theaters_collection = connect_to_mongodb()
    
    try:
        # Show database info
        print(f"\nConnected to MongoDB database: {MONGODB_DATABASE}")
        
        # Show collections
        collections = db.list_collection_names()
        print(f"Collections: {', '.join(collections)}")
        
        # Show basic counts
        show_city_count(cities_collection)
        show_theater_count(theaters_collection)
        
        # Show top cities
        show_top_cities(cities_collection)
        
        # Show theaters by city
        show_theaters_by_city(theaters_collection, cities_collection)
        
        # Show most recent theaters
        show_recent_theaters(theaters_collection)
        
        # Ask if user wants to export data
        export_choice = input("\nDo you want to export data to JSON files? (y/n): ")
        if export_choice.lower() == 'y':
            export_cities_json(cities_collection)
            export_theaters_json(theaters_collection)
    
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Close MongoDB connection
        client.close()
        print("\nMongoDB connection closed.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--theaters":
            # Show theaters for a specific city
            city_name = sys.argv[2] if len(sys.argv) > 2 else None
            client, db, cities_collection, theaters_collection = connect_to_mongodb()
            show_theaters_by_city(theaters_collection, cities_collection, city_name)
            client.close()
        elif sys.argv[1] == "--export":
            # Export data to JSON files
            client, db, cities_collection, theaters_collection = connect_to_mongodb()
            export_cities_json(cities_collection)
            export_theaters_json(theaters_collection)
            client.close()
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python show_cities.py                  - Show all statistics")
            print("  python show_cities.py --theaters [city] - Show theaters for a specific city")
            print("  python show_cities.py --export         - Export data to JSON files")
            print("  python show_cities.py --help           - Show this help message")
    else:
        main() 