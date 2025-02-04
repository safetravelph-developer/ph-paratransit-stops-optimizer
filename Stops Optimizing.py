import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import folium
from folium.plugins import MarkerCluster
import seaborn as sns
import geopandas as gpd
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
import contextily as ctx

# Load the boarding data
workdir = r"C:\Users\SafeTravelPH\Documents\Parasol Files"
combined_data = pd.read_csv(f"{workdir}/BA_Summary_Route_9_17.csv")

# Filter data for non-null boarding and alighting points
boarding_data = combined_data[(combined_data['Board'].notna()) | (combined_data['Alight'].notna())]
boarding_data = boarding_data.dropna(subset=['Lng', 'Lat'])

# K-means clustering
coordinates = boarding_data[['Lng', 'Lat']].values
num_clusters = 26
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
boarding_data['Cluster'] = kmeans.fit_predict(coordinates)

# Calculate centroids for each cluster
centroids = boarding_data.groupby('Cluster')[['Lng', 'Lat']].mean()

# Add "Cluster" column 
centroids['Cluster'] = centroids.index + 1

# Save clustered centroids to CSV 
centroids.to_csv(f"{workdir}/clustered_centroids.csv", index=False)

# Load the GTFS shapes data
gtfs_shapes_1 = pd.read_csv(r"C:\Users\SafeTravelPH\Downloads\shapes_r9.txt")
shapes_gdf_1 = gtfs_shapes_1.groupby('shape_id').apply(
    lambda group: LineString(list(zip(group['shape_pt_lon'], group['shape_pt_lat']))))
shapes_gdf_1 = gpd.GeoDataFrame(shapes_gdf_1.reset_index(name='geometry'), geometry='geometry', crs='EPSG:4326')

gtfs_shapes_2 = pd.read_csv(r"C:\Users\SafeTravelPH\Downloads\shapes_r17.txt")
shapes_gdf_2 = gtfs_shapes_2.groupby('shape_id').apply(
    lambda group: LineString(list(zip(group['shape_pt_lon'], group['shape_pt_lat']))))
shapes_gdf_2 = gpd.GeoDataFrame(shapes_gdf_2.reset_index(name='geometry'), geometry='geometry', crs='EPSG:4326')

# Combine shape files into one GeoDataFrame
shapes_gdf = pd.concat([shapes_gdf_1, shapes_gdf_2], ignore_index=True)

# Load clustered stops and convert to GeoDataFrame
clustered_stops = pd.read_csv(f"{workdir}/clustered_centroids.csv")
clustered_stops['geometry'] = gpd.GeoSeries.from_xy(clustered_stops['Lng'], clustered_stops['Lat'])
clustered_gdf = gpd.GeoDataFrame(clustered_stops, geometry='geometry', crs='EPSG:4326')

# Assign clustered stops to nearest route segment and snap them
assignments = []
for idx, stop in clustered_gdf.iterrows():
    stop_point = stop['geometry']
    min_distance = float("inf")
    nearest_route_id, snapped_stop_point = None, None

    for _, shape in shapes_gdf.iterrows():
        route_line = shape['geometry']
        nearest_geom = nearest_points(stop_point, route_line)[1]
        distance = stop_point.distance(nearest_geom)

        if distance < min_distance:
            min_distance = distance
            nearest_route_id = shape['shape_id']
            snapped_stop_point = nearest_geom

    assignments.append({
        'Cluster': stop['Cluster'],
        'nearest_route_id': nearest_route_id,
        'distance_to_route': min_distance,
        'snapped_lat': snapped_stop_point.y,
        'snapped_lon': snapped_stop_point.x
    })

# Create DataFrame for assignments
assignments_df = pd.DataFrame(assignments)

# Merge the assignments with the clustered stops
aligned_cluster_stops = clustered_gdf.merge(assignments_df, on="Cluster", how="left")

output_df = aligned_cluster_stops[['Cluster', 'snapped_lon', 'snapped_lat', 'geometry']].copy()

# Save the final output to CSV
output_csv_path = f"{workdir}/Aligned_clustered_stops.csv"
output_df.to_csv(output_csv_path, index=False)

# Visualize the results with a base map
fig, ax = plt.subplots(figsize=(10, 10))

shapes_gdf_1.plot(ax=ax, color='blue', linewidth=1, label="Route 9 Line Route")
shapes_gdf_2.plot(ax=ax, color='green', linewidth=1, label="Route 17 Line Route")
clustered_gdf.plot(ax=ax, color='red', marker='o', label="Clustered Stops", markersize=7)

snapped_gdf = aligned_cluster_stops.dropna(subset=['snapped_lat', 'snapped_lon'])
snapped_gdf['geometry'] = gpd.GeoSeries.from_xy(snapped_gdf['snapped_lon'], snapped_gdf['snapped_lat'])
snapped_gdf.plot(ax=ax, color='black', marker='o', label="Aligned Stops", markersize=10)

ctx.add_basemap(ax, crs=shapes_gdf_1.crs.to_string(), source=ctx.providers.CartoDB.Positron)

plt.legend()
plt.show()

print(output_df.head())
