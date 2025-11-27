import folium
import xml.etree.ElementTree as ET
import webbrowser
import os

def create_map_from_kml(kml_filename, output_map_name="wargame_map.html"):
    """
    Parses a KML file and generates an interactive HTML map.
    """
    
    # 1. Parse the KML File
    try:
        # Check if file is empty
        if os.stat(kml_filename).st_size == 0:
            print(f"Error: The file '{kml_filename}' is empty.")
            return

        tree = ET.parse(kml_filename)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: Could not find file '{kml_filename}'. Please ensure it exists.")
        return
    except ET.ParseError as e:
        print(f"Error: Could not parse '{kml_filename}'. It might be empty or invalid XML.\nDetails: {e}")
        return

    # KML files use a namespace, we need to handle it to find tags
    # The structure is usually {http://www.opengis.net/kml/2.2}TagName
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}

    # 2. Initialize the Map
    # We'll center it on the UK initially (approx lat 54, lon -2)
    m = folium.Map(location=[54.5, -3.0], zoom_start=6, tiles="OpenStreetMap")

    # 3. Extract Placemarks and add to Map
    # We search for all 'Placemark' tags within the namespace
    placemarks = root.findall('.//kml:Placemark', namespace)
    
    print(f"Found {len(placemarks)} locations in KML.")

    for placemark in placemarks:
        # Extract Name
        name_tag = placemark.find('kml:name', namespace)
        name = name_tag.text if name_tag is not None else "Unknown Location"

        # Extract Description
        desc_tag = placemark.find('kml:description', namespace)
        description = desc_tag.text if desc_tag is not None else ""

        # Extract Coordinates
        point = placemark.find('.//kml:Point/kml:coordinates', namespace)
        if point is not None:
            coords_str = point.text.strip()
            # KML is Longitude,Latitude,Altitude
            try:
                lon, lat, _ = coords_str.split(',')
                
                # Folium requires Latitude, Longitude
                lat = float(lat)
                lon = float(lon)

                # Create a marker
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(f"<b>{name}</b><br>{description}", max_width=300),
                    tooltip=name,
                    icon=folium.Icon(color="red", icon="info-sign")
                ).add_to(m)
            except ValueError:
                print(f"Skipping placemark '{name}': Invalid coordinates format.")

    # 4. Save the map
    m.save(output_map_name)
    print(f"Map saved to {output_map_name}")

    # 5. Open in Browser automatically
    file_path = os.path.abspath(output_map_name)
    webbrowser.open(f'file://{file_path}')

if __name__ == "__main__":
    # Ensure you have saved the previous KML output as 'locations.kml'
    create_map_from_kml("data/wargame_locations.kml")