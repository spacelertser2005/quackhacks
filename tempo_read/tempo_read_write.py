import requests
import os
import zstandard as zstd
import time
import csv
from netCDF4 import Dataset
import pandas as pd
from joblib import Parallel, delayed
import subprocess

secure = dict([e.split('=') for e in open('secure.txt', 'r').read().split('\n')])

tempo_row_dir = 'tempo_rows.txt'
rows = [line.strip() for line in open(tempo_row_dir, 'r') if line.strip()]
download_dir = '/tmp/'

from netCDF4 import Dataset
import os, csv

# Extracts variables from the NetCDF file and writes it into a CSV file 
def extract_var_and_wr_csv(file_dir, output_csv_path, original_row):
    """
    Process NetCDF files in a given directory to extract metadata and write to a CSV file, 
    including the original download URL and selected TEMPO variables.
    """
    # List all NetCDF files in the specified directory
    files = [f for f in os.listdir(file_dir) if f.endswith('.nc')]

    # Headers: metadata + science variables
    headers = [
        'granule_id',
        'original_row',
        'time_start',
        'time_end',
        'product',
        'location',
        'split',
        'granuleSize',
        'vertical_column_troposphere',
        'eff_cloud_fraction',
        'solar_zenith_angle',
        'viewing_zenith_angle',
        'surface_pressure',
        'terrain_height',
        'main_data_quality_flag',
        'ground_pixel_quality_flag',
        'fit_rms_residual',
        'amf_troposphere'
    ]

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    def find_var(nc, name):
        """Search root and all subgroups for a variable with this name."""
        if name in nc.variables:
            return nc.variables[name]
        for g in nc.groups.values():
            if name in g.variables:
                return g.variables[name]
            # one more level deep just in case
            for sg in g.groups.values():
                if name in sg.variables:
                    return sg.variables[name]
        return None

    def get_scalar(nc, name):
        """Return a single representative value (first finite element) for a variable."""
        var = find_var(nc, name)
        if var is None:
            return ''
        data = var[:].flatten()
        # Handle masked arrays
        try:
            data = data.compressed()
        except AttributeError:
            pass
        for v in data:
            # skip fill/NaN-like values
            try:
                if v is not None and v == v:  # v == v filters out NaN
                    return float(v)
            except Exception:
                continue
        return ''

    file_exists = os.path.exists(output_csv_path)
    with open(output_csv_path, 'a', newline='') as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=headers)

        if not file_exists or os.stat(output_csv_path).st_size == 0:
            csvwriter.writeheader()  # Write header only if file is empty

        for file_name in files:
            file_path = os.path.join(file_dir, file_name)
            with Dataset(file_path, 'r') as nc:
                # Metadata
                timeStart = getattr(nc, 'time_coverage_start', 'NA')
                timeEnd   = getattr(nc, 'time_coverage_end', 'NA')
                product   = 'tempo'
                location  = 'la'
                split     = 'train'
                granuleSize = os.path.getsize(file_path)

                # Science variables (one scalar per granule)
                vct = get_scalar(nc, 'vertical_column_troposphere')
                ecf = get_scalar(nc, 'eff_cloud_fraction')
                sza = get_scalar(nc, 'solar_zenith_angle')
                vza = get_scalar(nc, 'viewing_zenith_angle')
                sp  = get_scalar(nc, 'surface_pressure')
                th  = get_scalar(nc, 'terrain_height')
                mqf = get_scalar(nc, 'main_data_quality_flag')
                gqf = get_scalar(nc, 'ground_pixel_quality_flag')
                rms = get_scalar(nc, 'fit_rms_residual')
                amf = get_scalar(nc, 'amf_troposphere')

                csvwriter.writerow({
                    'granule_id': file_name,
                    'original_row': original_row,
                    'time_start': timeStart,
                    'time_end': timeEnd,
                    'product': product,
                    'location': location,
                    'split': split,
                    'granuleSize': granuleSize,
                    'vertical_column_troposphere': vct,
                    'eff_cloud_fraction': ecf,
                    'solar_zenith_angle': sza,
                    'viewing_zenith_angle': vza,
                    'surface_pressure': sp,
                    'terrain_height': th,
                    'main_data_quality_flag': mqf,
                    'ground_pixel_quality_flag': gqf,
                    'fit_rms_residual': rms,
                    'amf_troposphere': amf
                })
            print(f"Successfully Written: {file_name}")

# Removes the netcdf files in tmp to save storage space
def os_remove():
    tmp_dir = '/tmp/'  # The directory from which you want to delete files
    files = [f for f in os.listdir(tmp_dir) if f.endswith('.nc')]  # List of all .nc files in the directory
    
    for filename in files:
        file_path = os.path.join(tmp_dir, filename)  # Full path to the file
        try:
            os.remove(file_path)  # Delete the file
            print(f"Successfuly Deleted: {filename} from {tmp_dir}")
        except FileNotFoundError:  # Catch the specific exception if the file does not exist
            print(f"{filename} does not exist")

def loadFileS3(rows):
    for i in range(1):
        try:
            values = {'email' : secure['username'], 'passwd' : secure['password'], 'action' : 'login'}
            login_row = 'https://urs.earthdata.nasa.gov'
            ret = requests.post(login_row, data=values)
            if ret.status_code == 200:
                print("Login successful.")
            else:
                print("Bad Authentication")
                return None
        except Exception as e:
            print(e)
            time.sleep(i)
        
    os.makedirs(download_dir, exist_ok=True)
    for row in rows:
        try:
            outfile = os.path.basename(row)
            print("Downloading", outfile)
            with requests.get(row, cookies = ret.cookies, 
                              allow_redirects = True, stream=True) as r:
                r.raise_for_status()
                outfile_path = os.path.join(download_dir, outfile)
                with open(outfile_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024): 
                        f.write(chunk)
                  
            filename = row.split('/')[-1]
            save_path = os.path.join(download_dir, filename)
            print(f"Downloaded and compressed {filename} to {save_path}")
            print("Extracting variables and writing to CSV.")
            extract_var_and_wr_csv('C:/tmp/', 'C:/csv/output.csv', row)
        except requests.RequestException as e:
            print(f"Error downloading {row}: {e}")
        finally:
            print("Deleting: TEMPO File")
            os_remove()
        
    return save_path

loadFileS3(rows)