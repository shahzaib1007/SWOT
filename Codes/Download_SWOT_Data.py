import os
import shutil
import xarray as xr
import earthaccess
from datetime import datetime, timedelta
import geopandas as gpd
import numpy as np
import warnings
import logging

# Suppress warnings
warnings.filterwarnings("ignore")

data_path = r"/water3/skhan7/SWOT_BD_Tripura/"

# Create a log folder if it doesn't exist
log_folder = rf"{data_path}/Logs/"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
    os.makedirs(f"{data_path}/Downloaded_Data/", exist_ok=True)
    os.makedirs(f"{data_path}/Filtered_Data/", exist_ok=True)


# Generate a log file name with the current date and time in YMDHHMMSS format
log_file_name = datetime.now().strftime("log_%Y%m%d%H%M%S.log")

# Configure logging to use the dynamically generated log file name
logging.basicConfig(
    filename=os.path.join(log_folder, log_file_name),
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logging.info("Starting the data download and processing script.")

try:
    auth = earthaccess.login(strategy='netrc')
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=18)).strftime('%Y-%m-%d')
    logging.info(f"Start date {start_date} and end date {end_date} for granules search.")
    results = earthaccess.search_data(
        short_name="SWOT_L2_HR_Raster_2.0",
        bounding_box=(89.7, 17.0, 94.9, 25.75),
        granule_name='*100m*PIC*_01',
        temporal=(str(start_date), str(end_date)),
    )

    logging.info(f"Found {len(results)} granules for the given search criteria.")

    filtered_results = []
    for granule in results:
        data_urls = granule.data_links()
        for url in data_urls:
            if 'SWOT_L2_HR_Raster_100m' in url:
                # Extract the date from the granule metadata
                date_str = granule.get("umm")['TemporalExtent']['RangeDateTime']['EndingDateTime']
                date_obj = datetime.fromisoformat(date_str.rstrip('Z'))  # Remove 'Z' and parse
                
                # Log the date of each granule found
                logging.info(f"Found granule with date: {date_obj.strftime('%Y-%m-%d')}")

                filtered_results.append((date_obj, granule))
                break

    geojson_file = rf"{data_path}/Codes/east-bengal.geojson"
    geojson = gpd.read_file(geojson_file)
    utm45_crs = "EPSG:32645"
    utm46_crs = "EPSG:32646"
    utm44_crs = "EPSG:32644"
    geojson_utm = geojson.to_crs(utm45_crs)

    for date_obj, granule in filtered_results:
        download_url = granule.data_links()[0]
        local_path = rf"{data_path}/Downloaded_Data/SWOT_BD_{date_obj.strftime('%Y%m%d')}_{granule['umm']['RelatedUrls'][0]['URL'].split('x_x_x')[1].split('F')[0]}"
        
        # Download the file
        logging.info(f"Downloading file from {download_url} to {local_path}.")
        earthaccess.download(download_url, local_path=local_path)
        native_id = granule.get('meta')['native-id']

        # Load the NetCDF file using xarray
        ds = xr.open_dataset(f'{local_path}/{native_id}.nc')
        ds = ds.astype('float32') 
        quantile_low = np.float32(ds['wse'].quantile(0.05).item())
        quantile_high = np.float32(ds['wse'].quantile(0.95).item())
        logging.info(f"Quantiles for wse: low={quantile_low}, high={quantile_high}")

        condition_1 = ds['wse'] >= quantile_low
        condition_2 = ds['wse'] <= quantile_high
        ds = ds.where(condition_1, drop=True).where(condition_2, drop=True)

        if "UTM46" in granule.get('meta')['native-id']:
            logging.info(f"Reprojecting {native_id} from UTM Zone 46 to UTM Zone 45.")
            ds.rio.write_crs(utm46_crs, inplace=True)
            ds_utm = ds.rio.reproject(utm45_crs)
        elif "UTM45" in native_id:
            logging.info(f"File {native_id} is already in UTM Zone 45. Writing CRS as UTM45.")
            ds.rio.write_crs(utm45_crs, inplace=True)
            ds_utm = ds
        elif "UTM44" in granule.get('meta')['native-id']:
            logging.info(f"Reprojecting {native_id} from UTM Zone 44 to UTM Zone 45.")
            ds.rio.write_crs(utm44_crs, inplace=True)
            ds_utm = ds.rio.reproject(utm45_crs)
        else:
            logging.warning(f"File {native_id} does not contain UTM information. Skipping.")
            pass

        try:
            ds_filtered = ds_utm.rio.clip(geojson_utm.geometry, geojson_utm.crs)
            wse_filtered = ds_filtered[['wse']]
        except Exception as e:
            logging.error(f"Error while clipping data for {native_id}: {e}")
            continue

        output_path = f"{data_path}/Filtered_Data/SWOT_BD_{date_obj.strftime('%Y%m%d')}_{native_id.split('x_x_x_')[1].split('F')[0]}_wse.nc"
        wse_filtered.to_netcdf(output_path)
        logging.info(f"Saved filtered data to {output_path}")

        # Close the dataset
        ds.close()

        # Delete the original NetCDF file
        if os.path.isdir(local_path):
            try:
                shutil.rmtree(local_path)
                logging.info(f"Deleted the directory and its contents: {local_path}")
            except PermissionError as e:
                logging.warning(f"Permission error while deleting {local_path}: {e}")
        else:
            logging.warning(f"Directory not found: {local_path}")

        # Add a big log entry when finished with a granule
        logging.info("*******************************************************")
        logging.info(f"Finished processing granule for date: {date_obj.strftime('%Y-%m-%d')}")
        logging.info("*******************************************************")

except Exception as e:
    logging.error(f"An error occurred: {e}")

logging.info("Script finished successfully.")
