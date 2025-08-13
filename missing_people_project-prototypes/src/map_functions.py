import dash_leaflet as dl
from dash import html, dcc
import pandas as pd
import numpy as np
import ast
from collections import defaultdict
from utils.date_from_report_id import date_from_reportid


def create_summ_mp_missing_from_found_locations_map(df, locations):
    """
    Creates a map component from a dataframe with location columns.
    Uses colored dots that scale in size based on frequency.
    Only includes coordinates within UK boundaries.
    Also displays addresses that couldn't be plotted and addresses that were successfully plotted.
    
    Args:
        df: DataFrame with 'missing_from_latlong', 'tl_latlong', 'home_latlong', and 'reporid' columns
            containing tuples of [longitude, latitude] or [None, None]
    
    Returns:
        html.Details component containing the map, unplottable addresses, and plottable addresses
    """
    
    
    print("MMMMMM", locations)
    
    def is_within_uk(lat, lon):
        """
        Check if coordinates are within UK boundaries.
        UK approximate boundaries:
        - Latitude: 49.5 to 61.0 (includes Shetland Islands)
        - Longitude: -8.5 to 2.0 (includes Northern Ireland and eastern England)
        """
        if lat is None or lon is None:
            return False
        return 49.5 <= lat <= 61.0 and -8.5 <= lon <= 2.0
    
    def get_optimal_map_center_and_zoom(valid_locations):
        """
        Calculate optimal center and zoom level for the map based on location distribution.
        """
        if not valid_locations:
            # Default to UK center if no valid locations
            return [54.5, -2.5], 6
        
        # Extract lat/lon arrays
        lats = [loc[0] for loc in valid_locations]
        lons = [loc[1] for loc in valid_locations]
        
        # Calculate bounds
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # Calculate center
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # Calculate span to determine zoom level
        lat_span = max_lat - min_lat
        lon_span = max_lon - min_lon
        max_span = max(lat_span, lon_span)
        
        # Determine zoom level based on span
        if max_span > 8:  # Very large area (multiple countries)
            zoom = 5
        elif max_span > 4:  # Large area (entire UK)
            zoom = 6
        elif max_span > 2:  # Regional area
            zoom = 7
        elif max_span > 1:  # City/county level
            zoom = 8
        elif max_span > 0.5:  # City area
            zoom = 9
        elif max_span > 0.1:  # Local area
            zoom = 11
        elif max_span > 0.05:  # Neighborhood
            zoom = 12
        else:  # Very local area
            zoom = 13
        
        # Add some padding by reducing zoom slightly for better view
        zoom = max(zoom - 1, 5)  # Minimum zoom of 5
        
        return [center_lat, center_lon], zoom
    
    # Track location frequencies, types, and report IDs
    location_data = defaultdict(lambda: {'missing': 0, 'found': 0, 'home': 0, 'missing_reportids': [], 'found_reportids': [], 'home_reportids': []})
    polylines = []
    valid_locations = []
    
    # Track unplottable and plottable addresses
    unplottable_addresses = {
        'Missing From': [],
        'Found At': [],
        'Home Address': [],
        
    }
    other_addresses = {
        'Other': []
    }
    for l in locations:
        other_addresses['Other'].append({
        'address': l[0],
        'report_id': l[2][0] if l[2][0] else None
    })
    plottable_addresses = {
        'Missing From': [],
        'Found At': [],
        'Home Address': []
    }
    
    
    # First pass: count occurrences of each location and collect report IDs
    for idx in range(len(df)):
        missing_location = None
        tl_location = None
        
        # Get report ID for this row
        reporid = df['reportid'].iloc[idx] if 'reportid' in df.columns and idx < len(df['reportid']) else f"Row {idx + 1}"
        
        # Process missing_from_latlong
        if 'missing_from_latlong' in df.columns and idx < len(df['missing_from_latlong']):
            location_str = df['missing_from_latlong'].iloc[idx]
            mf_address = df['mf_address'].iloc[idx] if 'mf_address' in df.columns and idx < len(df['mf_address']) else "Unknown Address"
            
            if location_str and location_str != '[None, None]':
                try:
                    location = check_valid_loc(ast.literal_eval(location_str))
                    if location is not None and location != [None, None] and len(location) == 2:
                        lon, lat = location
                        if lon is not None and lat is not None:
                            missing_location = [lat, lon]
                            # Round to avoid slight coordinate differences
                            coord_key = (round(lat, 6), round(lon, 6))
                            location_data[coord_key]['missing'] += 1

                            if mf_address not in location_data[coord_key]['missing_reportids']:
                                location_data[coord_key]['missing_reportids'].append(mf_address)
                            location_data[coord_key]['found_reportids'].append(str(reporid))

                            valid_locations.append([lat, lon])
                            
                            # Add to plottable addresses
                            if mf_address:
                                plottable_addresses['Missing From'].append({
                                    'address': mf_address,
                                    'report_id': str(reporid),
                                    'coordinates': f"{lat:.6f}, {lon:.6f}"
                                })
                        else:
                            # Coordinates are None - address couldn't be plotted
                            if mf_address:
                                unplottable_addresses['Missing From'].append({
                                    'address': mf_address,
                                    'report_id': str(reporid)
                                })
                    else:
                        # Invalid location - address couldn't be plotted
                        if mf_address:
                            unplottable_addresses['Missing From'].append({
                                'address': mf_address,
                                'report_id': str(reporid)
                            })
                except (ValueError, SyntaxError):
                    # Failed to parse location - address couldn't be plotted
                    if mf_address:
                        unplottable_addresses['Missing From'].append({
                            'address': mf_address,
                            'report_id': str(reporid)
                        })
            else:
                # No location string - address couldn't be plotted
                if mf_address:
                    unplottable_addresses['Missing From'].append({
                        'address': mf_address,
                        'report_id': str(reporid)
                    })
        
        # Process tl_latlong
        if 'tl_latlong' in df.columns and idx < len(df['tl_latlong']):
            location_str = df['tl_latlong'].iloc[idx]
            tl_address = df['tl_address'].iloc[idx] if 'tl_address' in df.columns and idx < len(df['tl_address']) else "Unknown Address"
            
            if location_str and location_str != '[None, None]':
                try:
                    location = check_valid_loc(ast.literal_eval(location_str))
                    if location is not None and location != [None, None] and len(location) == 2:
                        lon, lat = location
                        if lon is not None and lat is not None:
                            tl_location = [lat, lon]
                            # Round to avoid slight coordinate differences
                            coord_key = (round(lat, 6), round(lon, 6))
                            location_data[coord_key]['found'] += 1
                            
                            if tl_address not in location_data[coord_key]['found_reportids']:
                                location_data[coord_key]['found_reportids'].append(tl_address)
                            location_data[coord_key]['found_reportids'].append(str(reporid))
                            
                            valid_locations.append([lat, lon])
                            
                            # Add to plottable addresses
                            if tl_address:
                                plottable_addresses['Found At'].append({
                                    'address': tl_address,
                                    'report_id': str(reporid),
                                    'coordinates': f"{lat:.6f}, {lon:.6f}"
                                })
                        else:
                            # Coordinates are None - address couldn't be plotted
                            if tl_address :
                                unplottable_addresses['Found At'].append({
                                    'address': tl_address,
                                    'report_id': str(reporid)
                                })
                    else:
                        # Invalid location - address couldn't be plotted
                        if tl_address:
                            unplottable_addresses['Found At'].append({
                                'address': tl_address,
                                'report_id': str(reporid)
                            })
                except (ValueError, SyntaxError):
                    # Failed to parse location - address couldn't be plotted
                    if tl_address:
                        unplottable_addresses['Found At'].append({
                            'address': tl_address,
                            'report_id': str(reporid)
                        })
            else:
                # No location string - address couldn't be plotted
                if tl_address:
                    unplottable_addresses['Found At'].append({
                        'address': tl_address,
                        'report_id': str(reporid)
                    })
        
        # Process home_latlong
        if 'home_latlong' in df.columns and idx < len(df['home_latlong']):
            location_str = df['home_latlong'].iloc[idx]
            ha_address = df['ha_address'].iloc[idx] if 'ha_address' in df.columns and idx < len(df['ha_address']) else "Unknown Address"
            
            if location_str and location_str != '[None, None]':
                try:
                    location = check_valid_loc(ast.literal_eval(location_str))
                    if location is not None and location != [None, None] and len(location) == 2:
                        lon, lat = location
                        if lon is not None and lat is not None:
                            home_location = [lat, lon]
                            # Round to avoid slight coordinate differences
                            coord_key = (round(lat, 6), round(lon, 6))
                            location_data[coord_key]['home'] += 1
                            location_data[coord_key]['home_reportids'].append(str(reporid))
                            valid_locations.append([lat, lon])
                            
                            # Add to plottable addresses
                            if ha_address:
                                plottable_addresses['Home Address'].append({
                                    'address': ha_address,
                                    'report_id': str(reporid),
                                    'coordinates': f"{lat:.6f}, {lon:.6f}"
                                })
                        else:
                            # Coordinates are None - address couldn't be plotted
                            if ha_address :
                                unplottable_addresses['Home Address'].append({
                                    'address': ha_address,
                                    'report_id': str(reporid)
                                })
                    else:
                        # Invalid location - address couldn't be plotted
                        if ha_address :
                            unplottable_addresses['Home Address'].append({
                                'address': ha_address,
                                'report_id': str(reporid)
                            })
                except (ValueError, SyntaxError):
                    # Failed to parse location - address couldn't be plotted
                    if ha_address :
                        unplottable_addresses['Home Address'].append({
                            'address': ha_address,
                            'report_id': str(reporid)
                        })
            else:
                # No location string - address couldn't be plotted
                if ha_address :
                    unplottable_addresses['Home Address'].append({
                        'address': ha_address,
                        'report_id': str(reporid)
                    })
        
        # Create polyline connection if both locations exist
        if missing_location and tl_location:
            polylines.append(
                dl.Polyline(
                    positions=[missing_location, tl_location],
                    color="purple",
                    weight=2,
                    opacity=0.5,
                    dashArray="5, 10",
                    children=[
                        dl.Tooltip(f"Connection for Report ID: {reporid}")
                    ]
                )
            )
    
    # Create markers based on frequency
    markers = []
    home_markers = []
    
    for (lat, lon), data in location_data.items():
        missing_count = data['missing']
        found_count = data['found']
        home_count = data['home']
        total_count = missing_count + found_count + home_count
        missing_reportids = data['missing_reportids']
        found_reportids = data['found_reportids']
        home_reportids = data['home_reportids']
        
        # Create tooltip text with report IDs
        tooltip_parts = []
        if missing_count > 0:
            missing_ids = ", ".join(missing_reportids[:5])  # Show first 5 IDs
            if len(missing_reportids) > 5:
                missing_ids += f" (and {len(missing_reportids) - 5} more)"
            tooltip_parts.append(f"Missing ({missing_count}): {missing_ids}")
        
        if found_count > 0:
            found_ids = ", ".join(found_reportids[:5])  # Show first 5 IDs
            if len(found_reportids) > 5:
                found_ids += f" (and {len(found_reportids) - 5} more)"
            tooltip_parts.append(f"Found ({found_count}): {found_ids}")
        
        if home_count > 0:
            home_ids = ", ".join(home_reportids[:5])  # Show first 5 IDs
            if len(home_reportids) > 5:
                home_ids += f" (and {len(home_reportids) - 5} more)"
            tooltip_parts.append(f"Home ({home_count}): {home_ids}")
        
        tooltip_text = "\n".join(tooltip_parts) + f"\nTotal: {total_count}"
        
        # If there's a home location, ALWAYS show the home icon
        if home_count > 0:
            home_markers.append(
                dl.Marker(
                    position=[lat, lon],
                    children=[
                        dl.Tooltip(tooltip_text)
                    ],
                    icon={
                        "iconUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='0.9em' font-size='60'%3E🏠%3C/text%3E%3C/svg%3E",
                        "iconSize": [30, 30],
                        "iconAnchor": [15, 15]
                    }
                )
            )
        
        # If there are missing/found locations, also show colored circle markers
        non_home_total = missing_count + found_count
        if non_home_total > 0:
            # Determine dot color based on predominant type (excluding home for color calculation)
            if missing_count > found_count:
                color = "#FF4444"  # Red for predominantly missing
                marker_type = "Missing"
            elif found_count > missing_count:
                color = "#44AA44"  # Green for predominantly found
                marker_type = "Found"
            else:
                color = "#AA44AA"  # Purple for equal counts
                marker_type = "Missing/Found (both)"
            
            # Scale radius based on frequency (min 8, max 30)
            base_radius = 8
            max_radius = 30
            radius = min(base_radius + (non_home_total - 1) * 3, max_radius)
            
            # If there's also a home location, make the circle slightly smaller and offset
            if home_count > 0:
                radius = max(radius - 5, 10)  # Make it smaller but not too small
                # Offset the position slightly so both markers are visible
                offset_lat = lat + 0.0001  # Small offset
                offset_lon = lon + 0.0001
            else:
                offset_lat = lat
                offset_lon = lon
            
            markers.append(
                dl.CircleMarker(
                    center=[offset_lat, offset_lon],
                    radius=radius,
                    children=[
                        dl.Tooltip(tooltip_text)
                    ],
                    color="white",
                    weight=2,
                    fillColor=color,
                    fillOpacity=0.8
                )
            )
            
            # Add small center point
            markers.append(
                dl.CircleMarker(
                    center=[offset_lat, offset_lon],
                    radius=3,
                    color="white",
                    weight=1,
                    fillColor="#333333",
                    fillOpacity=1.0
                )
            )
    
    # Calculate optimal center and zoom
    center, zoom = get_optimal_map_center_and_zoom(valid_locations)
    
    # Create size legend
    def create_size_example(radius, count):
        return html.Div([
            html.Div(style={
                'width': f'{radius}px',
                'height': f'{radius}px',
                'backgroundColor': '#888',
                'border': '2px solid white',
                'borderRadius': '50%',
                'display': 'inline-block',
                'marginRight': '8px',
                'verticalAlign': 'middle'
            }),
            html.Span(f"{count} occurrence{'s' if count != 1 else ''}", 
                     style={'fontSize': '16px', 'verticalAlign': 'middle'})
        ], style={'marginBottom': '3px'})
    
    # Enhanced legend with colors and sizes
    legend = html.Div([
        html.Div("Legend", style={'fontWeight': 'bold', 'marginBottom': '12px', 'fontSize': '13px'}),
        
        # Color legend
        html.Div("Colors:", style={'fontWeight': 'bold', 'fontSize': '16px', 'marginBottom': '4px'}),
        html.Div([
            html.Div(style={
                'width': '16px', 
                'height': '16px', 
                'backgroundColor': '#FF4444', 
                'border': '2px solid white',
                'display': 'inline-block',
                'marginRight': '5px',
                'borderRadius': '50%'
            }),
            html.Span("Missing", style={'fontSize': '12px'})
        ], style={'marginBottom': '2px'}),
        html.Div([
            html.Div(style={
                'width': '16px', 
                'height': '16px', 
                'backgroundColor': '#44AA44', 
                'border': '2px solid white',
                'display': 'inline-block',
                'marginRight': '5px',
                'borderRadius': '50%'
            }),
            html.Span("Found", style={'fontSize': '12px'})
        ], style={'marginBottom': '2px'}),
        html.Div([
            html.Div(style={
                'width': '16px', 
                'height': '16px', 
                'backgroundColor': '#AA44AA', 
                'border': '2px solid white',
                'display': 'inline-block',
                'marginRight': '5px',
                'borderRadius': '50%'
            }),
            html.Span("Equal Missing/Found", style={'fontSize': '10px'})
        ], style={'marginBottom': '2px'}),
        html.Div([
            html.Span("🏠", style={'fontSize': '16px', 'marginRight': '5px'}),
            html.Span("Home Address (always shown)", style={'fontSize': '12px'})
        ], style={'marginBottom': '8px'}),
        
        # Size legend
        html.Div("Sizes:", style={'fontWeight': 'bold', 'fontSize': '12px', 'marginBottom': '4px'}),
        create_size_example(16, 1),
        create_size_example(22, 3),
        create_size_example(28, 5),
        
        # Connection legend
        html.Hr(style={'margin': '8px 0'}),
        html.Div([
            html.Div(style={
                'width': '20px', 
                'height': '2px', 
                'backgroundColor': 'purple', 
                'display': 'inline-block',
                'marginRight': '5px',
                'backgroundImage': 'repeating-linear-gradient(to right, purple 0px, purple 3px, transparent 3px, transparent 6px)'
            }),
            html.Span("Connections", style={'fontSize': '12px'})
        ]),
        
        # Note about overlapping markers
        html.Hr(style={'margin': '8px 0'}),
        html.Div("Hover over markers to see Report IDs", style={'fontSize': '12px', 'fontStyle': 'italic', 'color': '#666'})
    ], style={
        'position': 'absolute',
        'top': '10px',
        'right': '10px',
        'backgroundColor': 'white',
        'padding': '16px',
        'border': '2px solid rgba(0,0,0,0.2)',
        'borderRadius': '5px',
        'zIndex': '1000',
        'fontSize': '11px',
        'maxWidth': '200px'
    })
    
    # Create map component with improved centering and zoom
    map_component = html.Div([
        dl.Map([
            dl.TileLayer(),
            *polylines,  # Add polylines first so they appear under markers
            *markers,
            *home_markers,  # Add home markers last so they appear on top
        ], style={'width': '100%', 'height': '600px'}, 
        center=center, zoom=zoom),
        legend
    ], style={"position": "relative"})
    
    # Create compact address items function
    def create_compact_address_items(addresses, icon, color, show_coordinates=False):
        if not addresses:
            return []
        
        # Remove duplicates while preserving order
        unique_addresses = []
        seen = set()
        for addr_info in addresses:
            addr_key = addr_info['address']
            if addr_key not in seen:
                unique_addresses.append(addr_info)
                seen.add(addr_key)
        
        items = []
        for addr_info in unique_addresses:
            item_content = [
                html.Span(icon, style={'marginRight': '4px', 'fontSize': '16px'}),
                html.Span(addr_info['address'], style={
                    'fontWeight': '500',
                    'fontSize': '12px',
                    'marginRight': '8px'
                }),
                date_from_reportid(addr_info['report_id'], "mp")
            ]
            
            # Add coordinates if requested (for plottable addresses)
            if show_coordinates and 'coordinates' in addr_info:
                item_content.append(
                    html.Span(f" ({addr_info['coordinates']})", style={
                        'fontSize': '9px',
                        'color': '#666',
                        'fontStyle': 'italic'
                    })
                )
            
            items.append(
                html.Div(item_content, style={
                    'display': 'inline-block',
                    'margin': '2px 8px 2px 0',
                    'padding': '3px 6px',
                    'backgroundColor': '#f8f9fa',
                    'border': f'1px solid {color}20',
                    'borderRadius': '3px',
                    'fontSize': '10px'
                })
            )
        return items
    
    # Create the unplottable addresses component
    unplottable_component = None
    other_component = None
    total_other = sum(len(addrs) for addrs in other_addresses.values())
    total_unplottable = sum(len(addrs) for addrs in unplottable_addresses.values())
    
    if total_unplottable > 0:
        all_unplottable_items = []
        
        # Add items for each address type
        all_unplottable_items.extend(create_compact_address_items(
            unplottable_addresses['Missing From'], "❌", "#FF4444"
        ))
        all_unplottable_items.extend(create_compact_address_items(
            unplottable_addresses['Found At'], "✅", "#44AA44"
        ))
        all_unplottable_items.extend(create_compact_address_items(
            unplottable_addresses['Home Address'], "🏠", "#AA6C39"
        ))
        
        unplottable_component = html.Details([
            html.Summary([
                html.Span(f"Addresses That Could Not Be Plotted ({total_unplottable})", style={
                    'fontSize': '16px',
                    'fontWeight': '600',
                    'color': '#d63384'
                })
            ], style={
                'cursor': 'pointer',
                'padding': '6px',
                'backgroundColor': '#fff5f5',
                'border': '1px solid #fed7d7',
                'borderRadius': '4px',
                'marginBottom': '8px'
            }),
            html.Div([
                html.P(
                    "Addresses that could not be geocoded (❌ - missing from, ✅ - found address, 🏠 - home address):",
                    style={'fontSize': '10px', 'color': '#666', 'margin': '8px 0 6px 0'}
                ),
                html.Div(all_unplottable_items, style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'gap': '2px'
                })
            ], style={'padding': '8px'})
        ], style={
            'marginTop': '16px',
            'backgroundColor': '#fff9f9',
            'border': '1px solid #fed7d7',
            'borderRadius': '6px'
        })
        
    if total_other > 0:
        all_other_items = []
        
        # Add items for each address type
        all_other_items.extend(create_compact_address_items(
            other_addresses['Other'], "🔵", "#FF4444"
        ))
    
        
        other_component = html.Details([
            html.Summary([
                html.Span(f"🤖Other recognized locations({total_other})", style={
                    'fontSize': '16px',
                    'fontWeight': '600',
                    'color': '#2664eb'
                })
            ], style={
                'cursor': 'pointer',
                'padding': '6px',
                'backgroundColor': '#e8f2ff',
                'border': '1px solid #2664eb',
                'borderRadius': '4px',
                'marginBottom': '8px'
            }),
            html.Div([
                html.Div(all_other_items, style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'gap': '2px'
                })
            ], style={'padding': '8px'})
        ], style={
            'marginTop': '16px',
            'backgroundColor': '#e8f2ff',
            'border': '1px solid #df2664ebe7fd',
            'borderRadius': '6px'
        })
    
    # Create the plottable addresses component
    plottable_component = None
    total_plottable = sum(len(addrs) for addrs in plottable_addresses.values())
    
    if total_plottable > 0:
        all_plottable_items = []
        
        # Add items for each address type
        all_plottable_items.extend(create_compact_address_items(
            plottable_addresses['Missing From'], "❌", "#FF4444", show_coordinates=True
        ))
        all_plottable_items.extend(create_compact_address_items(
            plottable_addresses['Found At'], "✅", "#44AA44", show_coordinates=True
        ))
        all_plottable_items.extend(create_compact_address_items(
            plottable_addresses['Home Address'], "🏠", "#AA6C39", show_coordinates=True
        ))
        
        plottable_component = html.Details([
            html.Summary([
                html.Span(f"Successfully Plotted Addresses", style={
                    'fontSize': '16px',
                    'fontWeight': '600',
                    'color': '#28a745'
                })
            ], style={
                'cursor': 'pointer',
                'padding': '6px',
                'backgroundColor': '#f8fff8',
                'border': '1px solid #d4edda',
                'borderRadius': '4px',
                'marginBottom': '8px'
            }),
            html.Div([
                html.P(
                    "Addresses that were successfully geocoded and plotted on the map (❌ - missing from, ✅ - found address, 🏠 - home address):",
                    style={'fontSize': '12px', 'color': '#666', 'margin': '8px 0 6px 0'}
                ),
                html.Div(all_plottable_items, style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'gap': '2px'
                })
            ], style={'padding': '8px'})
        ], style={
            'marginTop': '16px',
            'backgroundColor': '#f8fff8',
            'border': '1px solid #d4edda',
            'borderRadius': '6px'
        })
    
    # Calculate statistics
    connection_count = len(polylines)
    unique_locations = len(location_data)
    total_occurrences = sum(data['missing'] + data['found'] + data['home'] for data in location_data.values())
    
    # Create the main content
    main_content = [map_component]
    if plottable_component:
        main_content.append(plottable_component)
    if unplottable_component:
        main_content.append(unplottable_component)
    if other_component:
        main_content.append(other_component)
    return html.Details([
        html.Summary([
            html.Div([
                html.H2("Map", className="locations-main-title"),
                html.Span(
                    f"{unique_locations} locations, {total_occurrences} total occurrences, "
                    f"{connection_count} connection{'s' if connection_count != 1 else ''}"
                    f"{f', {total_plottable} plottable addresses' if total_plottable > 0 else ''}"
                    f"{f', {total_unplottable} unplottable addresses' if total_unplottable > 0 else ''}", 
                    className="item-count-prominent"
                ),
                html.Span("▼", className="dropdown-arrow")
            ], className="locations-section-header-prominent")
        ], className="locations-summary-prominent"),
        html.Div(main_content, className="locations-dropdown-content")
    ], className="locations-section-prominent", open=True)
    
def check_valid_loc(location):
    lon, lat = location
    if lon is not None and lat is not None:
        # Check if coordinates are within UK bounds
        # UK approximate bounds: lat: 49.9 to 60.9, lon: -8.2 to 1.8
        if not (49.9 <= lat <= 60.9 and -8.2 <= lon <= 1.8):
            return [None, None]  # Skip this location as it's outside UK
    return location