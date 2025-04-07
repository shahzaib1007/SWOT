import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from datetime import datetime
from collections import defaultdict
import cartopy.io.img_tiles as cimgt
import calendar
import warnings
warnings.filterwarnings("ignore")

netcdf_dir = '../Filtered_Data/'

# Define custom boundaries for the ranges (initial boundaries can stay the same, but we'll update vmin/vmax per group)
boundaries = [0, 5, 10, 15, 20, 40, 60, 100, 500, 1000, 1600]

# Define a discrete colormap using a fixed list of colors
colors = ['#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
cmap = ListedColormap(colors)

# Group files by date (extract the date part from the filename)
files_by_date = defaultdict(list)
for file in os.listdir(netcdf_dir):
    if file.endswith('.nc'):
        date_part = file.split('_')[2]  # Extract date part (YYYYMMDD)
        files_by_date[date_part].append(file)

# Process each group of files that share the same date
for date, files in files_by_date.items():
    # year = date[:4]
    # month = int(date[4:6])
    # day = date[6:]
    # month_name = calendar.month_abbr[month] 
    # Calculate global min and max for this group of files
    date_obj = datetime.strptime(date, '%Y%m%d')
    formatted_date = date_obj.strftime('%d %b %Y')
    global_min = np.inf
    global_max = -np.inf
    for file in files:
        filepath = os.path.join(netcdf_dir, file)
        try:
            ds = xr.open_dataset(filepath)
            variable_name = 'wse'  # Change to your specific variable name
            data = ds[variable_name].values
            data_positive = ds[variable_name].where(ds[variable_name] >= 0, np.nan)  # Only positive values
            global_min = min(global_min, np.nanmin(data_positive))
            global_max = max(global_max, np.nanmax(data_positive))
            ds.close()
        except Exception as e:
            # print(f"Error processing {file}: {e}")
            continue
    
    # Initialize the figure and GeoAxes
    try:

        osm = cimgt.OSM()

        # Set up the map projection and axes
        fig = plt.figure(figsize=(12, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())

        # Add the OpenStreetMap basemap to the plot
        ax.add_image(osm, 10)  # The second argument is the zoom level (you can adjust this)

        # Add coastlines and borders (optional)
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linestyle=':')

        # Set extent (latitude and longitude bounds)
        ax.set_extent([89.6896, 96.1684, 17.0045, 25.7795], crs=ccrs.PlateCarree())
        gridlines = ax.gridlines(draw_labels=True, linestyle=':', color='gray', alpha=0.7)
        gridlines.top_labels = False  # Turn off labels at the top
        gridlines.right_labels = False  # Turn off labels on the right
        # Add a basemap (coastlines, borders, etc.)
        # ax.coastlines()
        # ax.add_feature(cfeature.BORDERS, linestyle=':')
        # ax.add_feature(cfeature.LAND, edgecolor='black')
        # ax.add_feature(cfeature.OCEAN)

        # Loop through each file for the current date and plot the data
        for file in files:
            filepath = os.path.join(netcdf_dir, file)
            try:
                # Open the dataset
                ds = xr.open_dataset(filepath)
                variable_name = 'wse'  # Change to your specific variable name
                data = ds[variable_name].where(ds['wse'] <= global_max, np.nan)
                data = ds[variable_name].where(ds['wse'] >= global_min, np.nan)
                # Assign coordinates if using x, y
                data = data.assign_coords(x=ds['x'], y=ds['y'])

                # Plot the data with discrete colormap and norm
                data.plot.pcolormesh(ax=ax, transform=ccrs.UTM(zone=45), cmap=cmap, vmin=global_min, vmax=global_max, add_colorbar=False)
                ds.close()
            except Exception as e:
                # print(f"Error processing {file}: {e}")
                continue

        # Add a colorbar with the discrete ranges, adjusted for global min/max
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=BoundaryNorm(boundaries, len(colors)))
        sm.set_array([])  # Empty array for colorbar mapping
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical',pad=0.02, label='Water Surface Elevation (wse)')
        cbar.set_ticks(boundaries)  # Place ticks at the boundaries
        tick_labels = [f'{b:.0f}m' for b in boundaries[:-1]]  # Set all except the last label
        tick_labels.append(f'>{boundaries[-1]:.0f}m')  # Append '>1600m' for the last label
        cbar.set_ticklabels(tick_labels)
        
        
        plt.title(f'SWOT WSE {formatted_date}')
        # ax.set_extent([773871.614859, 1337486.61732018, 1896118.07314831, 2855909.62618446])  # If you want to set a specific area
        # ax.set_extent([min_longitude, max_longitude, min_latitude, max_latitude])  # If you want to set a specific area
        ax.set_extent([89.68961819451815, 96.1684430301529, 17.004581710046345, 25.77955529545101])  
        
        ### Adding North Arrow ###
        ax.annotate('N', xy=(0.9, 0.95), xytext=(0.9, 0.9),
                    arrowprops=dict(facecolor='black', width=5, headwidth=15),
                    ha='center', va='center', fontsize=12,
                    xycoords=ax.transAxes)

        ### Adding Scale Bar ###
        def add_scalebar(ax, length_in_km, location=(0.1, 0.15), linewidth=3):
            # Get the x and y axis limits (extent of the map in lat/lon)
            x0, x1 = ax.get_xlim()
            y0, y1 = ax.get_ylim()

            # Calculate the scale bar length in degrees based on the scale (approx 1 degree = 111 km at equator)
            scale_length_deg = length_in_km / 111  # 111 km per degree

            # Calculate the position for the scale bar (adjust to be within the plot)
            x_start = x0 + (x1 - x0) * location[0]  # Adjust position based on map extent and location
            y_start = y0 + (y1 - y0) * location[1]  # Adjust position based on map extent and location

            # Draw the scale bar
            ax.plot([x_start, x_start + scale_length_deg], [y_start, y_start], color='black', linewidth=linewidth, transform=ccrs.PlateCarree())
            
            # Add the label for the scale bar
            ax.text((x_start + x_start + scale_length_deg) / 2, y_start+0.02 , f'{length_in_km} km',
                    ha='center', va='bottom', fontsize=10, transform=ccrs.PlateCarree())

        # Example of placing it dynamically within the map area
        add_scalebar(ax, length_in_km=100, location=(0.1, 0.05)) 
        # cbar.ax.set_position([1.5, 0.1, 0.03, 0.8])
        # Adjust layout to prevent overlap of grid labels and colorbar
        # plt.subplots_adjust(left=0.05, right=1, top=0.95, bottom=0.05)

        # fig.tight_layout()

        # Save the figure as a JPEG image for this date
        save_path = f'../Figures/Single_Date_Image/SWOT_{date}.jpeg'
        plt.savefig(save_path, dpi=1200, bbox_inches='tight')
        # plt.close(fig)
        # # Show the plot (optional)
        # plt.show()
        
        # Clear the figure for the next plot
        plt.clf()
    except:
        pass