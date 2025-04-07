import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
import cartopy.io.img_tiles as cimgt
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

# Directory containing your NetCDF files
netcdf_dir = '../Filtered_Data/'
output_dir = '../Figures/Mosaicked_Image/'

# Ensure output directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def get_files_within_days(target_date, days=10):
    """
    Get files within the last 'days' from the target_date (including target_date).
    """
    files = [file for file in os.listdir(netcdf_dir) if file.endswith('.nc')]
    files_within_days = []
    for file in files:
        file_date_str = file.split('_')[2]  # Extract date part from filename
        file_date = datetime.strptime(file_date_str, '%Y%m%d')  # Convert to datetime object

        # Include files with dates within 'days' before or on the target date
        if (target_date - timedelta(days=days)) <= file_date <= target_date:
            files_within_days.append((file, file_date))
    
    return files_within_days


def estimate_global_min_max(files_within_days):
    """
    Estimate global min and max values from the files.
    """
    global_min = np.inf
    global_max = -np.inf
    
    for file, file_date in files_within_days:
        filepath = os.path.join(netcdf_dir, file)
        try:
            ds = xr.open_dataset(filepath)
            data_positive = ds['wse'].where(ds['wse'] >= 0, np.nan)  # Only positive values
            global_min = min(global_min, np.nanmin(data_positive))
            global_max = max(global_max, np.nanmax(data_positive))
            ds.close()
        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue

    return global_min, global_max


def plot_wse(files_within_days, global_min, global_max, oldest_date, latest_date):
    """
    Plot the WSE for the selected files within the date range.
    """
    # Set up colormap and boundaries based on global min/max
    boundaries = [0, 5, 10, 15, 20, 40, 60, 100, 500, 1000, 1600]
    colors = ['#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#fc0516', '#a50026']
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(boundaries, len(colors))

    # Set up the map projection and axes
    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Add basemap (OpenStreetMap)
    osm = cimgt.OSM()
    ax.add_image(osm, 10)

    # Add coastlines and borders
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    # Set extent (latitude and longitude bounds)
    ax.set_extent([89.6896, 96.1684, 17.0045, 25.7795], crs=ccrs.PlateCarree())

    # Loop through each NetCDF file and plot the data
    for file, file_date in files_within_days:
        filepath = os.path.join(netcdf_dir, file)
        try:
            ds = xr.open_dataset(filepath)
            data_clipped = ds['wse'].where(ds['wse'] <= global_max, np.nan).assign_coords(x=ds['x'], y=ds['y'])
            data_clipped.plot.pcolormesh(ax=ax, transform=ccrs.UTM(zone=45), cmap=cmap, norm=norm, add_colorbar=False)
            ds.close()
        except Exception as e:
            print(f"Error processing {file}: {e}")
            continue

    # Add a colorbar (once at the end)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Empty array for colorbar mapping
    cbar = plt.colorbar(sm, ax=ax, orientation='vertical', pad=0.02, label='Water Surface Elevation (wse)')
    cbar.set_ticks(boundaries)
    tick_labels = [f'{b:.0f}m' for b in boundaries[:-1]]
    tick_labels.append(f'>{boundaries[-1]:.0f}m')
    cbar.set_ticklabels(tick_labels)

    # Adding North Arrow
    ax.annotate('N', xy=(0.9, 0.95), xytext=(0.9, 0.9),
                arrowprops=dict(facecolor='black', width=5, headwidth=15),
                ha='center', va='center', fontsize=12,
                xycoords=ax.transAxes)

    # Adding Scale Bar
    add_scalebar(ax, length_in_km=100, location=(0.1, 0.05))

    # Adding Gridlines
    gridlines = ax.gridlines(draw_labels=True, linestyle=':', color='gray', alpha=0.7)
    gridlines.top_labels = False
    gridlines.right_labels = False

    # Set plot title
    plt.title(f'SWOT WSE from {oldest_date.strftime("%d %b %Y")} to {latest_date.strftime("%d %b %Y")}')

    # Save plot
    output_filepath = os.path.join(output_dir, f'SWOT_Mosaicked_{latest_date.strftime("%Y%m%d")}.jpeg')
    plt.savefig(output_filepath, dpi=1200, bbox_inches='tight')
    plt.close(fig)  # Close the figure to avoid memory issues


def add_scalebar(ax, length_in_km, location=(0.1, 0.05), linewidth=3):
    """
    Add a scale bar to the map.
    """
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    scale_length_deg = length_in_km / 111  # 111 km per degree
    x_start = x0 + (x1 - x0) * location[0]
    y_start = y0 + (y1 - y0) * location[1]
    ax.plot([x_start, x_start + scale_length_deg], [y_start, y_start], color='black', linewidth=linewidth, transform=ccrs.PlateCarree())
    ax.text((x_start + x_start + scale_length_deg) / 2, y_start + 0.02, f'{length_in_km} km',
            ha='center', va='bottom', fontsize=10, transform=ccrs.PlateCarree())


def process_all_files():
    """
    Main function to loop over all NetCDF files and process them.
    Skips files if the corresponding image already exists.
    """
    files = [file for file in os.listdir(netcdf_dir) if file.endswith('.nc')]
    files.sort()

    # Loop over each file and process
    for file in files:
        # Extract the date from the filename (assuming it's in YYYYMMDD format)
        date_str = file.split('_')[2]
        target_date = datetime.strptime(date_str, '%Y%m%d')

        # Check if the image for this date already exists
        output_filepath = os.path.join(output_dir, f'SWOT_Mosaicked_{target_date.strftime("%Y%m%d")}.jpeg')
        if os.path.exists(output_filepath):
            # print(f"Image for {target_date.strftime('%Y%m%d')} already exists. Skipping...")
            continue  # Skip to the next file if the image exists

        # Find files within the last 10 days (only past files)
        files_within_days = get_files_within_days(target_date)

        # Estimate global min and max values
        global_min, global_max = estimate_global_min_max(files_within_days)

        # Get the oldest and latest date in the group
        dates_in_group = [file_date for _, file_date in files_within_days]
        oldest_date_in_group = min(dates_in_group)
        latest_date_in_group = max(dates_in_group)

        # Plot WSE
        plot_wse(files_within_days, global_min, global_max, oldest_date_in_group, latest_date_in_group)

if __name__ == "__main__":
    process_all_files()
