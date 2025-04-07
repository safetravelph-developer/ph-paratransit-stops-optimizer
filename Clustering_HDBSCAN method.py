import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
import contextily as ctx
import hdbscan
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import os

# Set working directory
workdir = r"C:\Users\SafeTravelPH\Documents\Parasol Files_Testing_hdbscan"

# Load boarding data
combined_data = pd.read_csv(f"{workdir}/BA_Summary_Route_9_17.csv")

# Filter data for non-null boarding/alighting points
boarding_data = combined_data[(combined_data['Board'].notna()) | (combined_data['Alight'].notna())]
boarding_data = boarding_data.dropna(subset=['Lng', 'Lat'])

# HDBSCAN Clustering
coordinates = boarding_data[['Lng', 'Lat']].values
clusterer = hdbscan.HDBSCAN(min_cluster_size=3, min_samples=1)
boarding_data['Cluster'] = clusterer.fit_predict(np.radians(coordinates))

# Remove noise points (-1 cluster label)
boarding_data = boarding_data[boarding_data['Cluster'] != -1]

# Calculate centroids for each cluster
centroids = boarding_data.groupby('Cluster')[['Lng', 'Lat']].mean().reset_index()

# Save clustered centroids to CSV
centroids.to_csv(f"{workdir}/route_9_17_clustered.csv", index=False)

# Load stop coordinate CSVs
stops_df1 = pd.read_csv(f"{workdir}/ROUTE_9_LU_STATIONS.csv")
stops_df2 = pd.read_csv(f"{workdir}/ROUTE_17_LU_STATIONS.csv")
stops_df = pd.concat([stops_df1, stops_df2], ignore_index=True)

# Convert to GeoDataFrame
stops_df['geometry'] = gpd.points_from_xy(stops_df['X'], stops_df['Y'])
stops_gdf = gpd.GeoDataFrame(stops_df, geometry='geometry', crs='EPSG:4326')

# Load clustered stops and convert to GeoDataFrame
clustered_stops = pd.read_csv(f"{workdir}/route_9_17_clustered.csv")
clustered_stops['Cluster'] = clustered_stops['Cluster'] + 1  
clustered_stops['geometry'] = gpd.points_from_xy(clustered_stops['Lng'], clustered_stops['Lat'])
clustered_gdf = gpd.GeoDataFrame(clustered_stops, geometry='geometry', crs='EPSG:4326')

# Snap clustered stops to nearest official stop
def snap_to_nearest_stop(stops_gdf, reference_gdf, min_snap_dist=300, max_snap_dist=500):
    min_snap_dist_deg = min_snap_dist / 111000  
    max_snap_dist_deg = max_snap_dist / 111000  
    snapped_stops = []
    used_points = []  
    
    for _, stop in stops_gdf.iterrows():
        stop_point = stop['geometry']
        valid_stops = [ref_point for ref_point in reference_gdf['geometry'].dropna()
                       if stop_point.distance(ref_point) <= max_snap_dist_deg]
        
        if valid_stops:
            valid_stops = sorted(valid_stops, key=stop_point.distance)
            for candidate_stop in valid_stops:
                if all(candidate_stop.distance(existing) >= min_snap_dist_deg for existing in used_points):
                    snapped_stops.append({'Cluster': stop['Cluster'], 'Lng': candidate_stop.x, 'Lat': candidate_stop.y, 'geometry': candidate_stop})
                    used_points.append(candidate_stop)
                    break  

    return gpd.GeoDataFrame(snapped_stops, geometry='geometry', crs='EPSG:4326')

clustered_gdf = snap_to_nearest_stop(clustered_gdf, stops_gdf)

# # Initialize Nominatim geocoder
geolocator = Nominatim(user_agent="geo_cluster")

def reverse_geocode(lat, lng, retries=3):
    """Reverse geocodes using Nominatim with retry handling."""
    for attempt in range(retries):
        try:
            location = geolocator.reverse((lat, lng), exactly_one=True)
            return location.address if location else "Unknown"
        except GeocoderTimedOut:
            print(f"Timeout error. Retrying ({attempt + 1}/{retries})...")
            time.sleep(2 ** attempt)  # Exponential backoff
    return "Failed"

# Apply reverse geocoding
print("Starting reverse geocoding...")
clustered_gdf['Address'] = clustered_gdf.apply(lambda row: reverse_geocode(row['Lat'], row['Lng']), axis=1)
print("Reverse geocoding completed!")

# Save final CSV
output_csv = f"{workdir}/clustered_geocoded_route9&17.csv"
clustered_gdf[['Cluster', 'Lng', 'Lat', 'Address']].to_csv(output_csv, index=False)
print(f"Geocoded stops data saved to {output_csv}")

#Visualization
fig, ax = plt.subplots(figsize=(10, 10))
stops_gdf.plot(ax=ax, color='blue', marker='o', label="Identified Stops", markersize=7)
clustered_gdf.plot(ax=ax, color='red', marker='o', label="Clustered Stops", markersize=5)
ctx.add_basemap(ax, crs=stops_gdf.crs.to_string(), source=ctx.providers.CartoDB.Positron)
plt.legend()

# Save visualization as PNG
output_img = f"{workdir}/output image.png"
plt.savefig(output_img, dpi=300, bbox_inches='tight')
print(f"Visualization saved as {output_img}")
plt.show()

# Save as shapefile
output_shp = f"{workdir}/output shapefile.shp"
clustered_gdf.to_file(output_shp, driver='ESRI Shapefile')
print(f"Shapefile saved to {output_shp}")
# Print first 5 rows of adjusted stops
print(clustered_gdf.head())
