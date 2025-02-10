# ph-paratransit-stops-optimizer

## Parasol Boarding & Alighting Data Processing

This repository contains Python code developed for the PARASOL Project, which aims to optimize formal/common stop identification for paratransit services (e.g., PUJs, PUBs, and trikes) using collected boarding and alighting data. The project is part of an effort to modernize public transport in Iloilo City by leveraging open data and advanced analytics.

## Overview
Purpose:
The code processes real-world boarding and alighting data from two intracity routes in Iloilo City. Using K-means clustering and GIS techniques, it identifies optimal stop locations by determining centroids of clustered data points and snapping them to the nearest route segments derived from GTFS shape files.

## Data Source:
The dataset used in this code is based on actual PUV trips from 2 out of 24 intracity routes in Iloilo City.

## Call to Action:
We invite developers, data scientists, and transport planners to collaborate with us on enhancing this tool. We are especially interested in contributions that incorporate accessibility considerations such as defining minimum and maximum distances between stops, integrating points of interest, and refining the placement of stops.

## What's inside?

Clustering:
Uses K-means clustering to group similar boarding/alighting events and calculates the centroid for each cluster.

GIS Integration:
Incorporates GTFS shapes data and uses GIS operations to snap cluster centroids to the nearest route segment.

Visualization:
Generates interactive maps using Folium to visualize raw clustered points and the aligned stop locations.

Output:
Produces a CSV file with the final aligned clustered stops along with the snapped coordinates and associated metadata.

Requirements
The code requires the following Python libraries:

pandas
numpy
matplotlib
scikit-learn
folium
seaborn
geopandas
shapely
contextily
You can install these dependencies using pip:

## Future Enhancements
We plan to extend this tool with additional features, including:

Accessibility Enhancements:
Incorporate criteria for minimum and maximum distances between stops and identify stops at key points of interest.
Integration with Smart Contract Modules:
Link operational data with performance-based incentives.
Enhanced Reporting:
Develop dashboards for real-time monitoring and reporting for public transport stakeholders.
Road Safety & Incident Reporting:
Integrate modules to report and evaluate road safety incidents.
Contributing
We welcome contributions to improve this code. If you have suggestions or enhancements, please submit a pull request or open an issue on GitHub. Let’s work together to build a smarter, more accessible public transport system!

## License
This project is licensed under the [MIT License](https://github.com/safetravelph-developer/ph-paratransit-stops-optimizer/blob/main/LICENSE).

## Contact
For more information, visit the [Parasol Project Website](https://safetravelph.org/parasol).
