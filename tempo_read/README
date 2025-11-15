🚀 TEMPO Data Downloader & NetCDF → CSV Extractor (Talipa Supercomputer Version)

This script downloads TEMPO NO₂ Level-2 NetCDF granules from NASA Earthdata, extracts selected variables, writes them into a single CSV file, and automatically deletes the NetCDF files to save storage on the cluster.

This README tells you exactly how to run it on Talipa / any HPC Linux cluster.

1. Files Needed

Place these files in the same directory:

tempo_read_write.py
tempo_rows.txt
secure.txt

tempo_rows.txt

A list of TEMPO .nc URLs, one per line. Example:

https://data.asdc.earthdata.nasa.gov/.../TEMPO_NO2_L2_V03_20240301.nc
https://data.asdc.earthdata.nasa.gov/.../TEMPO_NO2_L2_V03_20240301_2.nc

secure.txt

NASA Earthdata credentials (DO NOT COMMIT TO GIT):

username=YOUR_EMAIL_HERE
password=YOUR_EARTHDATA_PASSWORD

2. Recommended Directory Structure (on Talipa)
/home/<username>/tempo/
├─ tempo_read_write.py
├─ tempo_rows.txt
├─ secure.txt
├─ tmp/            # local temporary storage for NetCDFs
└─ csv/            # output CSV written here


Inside the script, the default paths are:

download_dir = '/tmp/'        # temporary location for .nc files
extract_dir  = 'C:/tmp/'      # change this (see below)
csv_output   = 'C:/csv/output.csv'  # change this (see below)


On Talipa these MUST be changed to Linux paths.

Change inside the Python code BEFORE running:

Replace:

extract_var_and_wr_csv('C:/tmp/', 'C:/csv/output.csv', row)
tmp_dir = '/tmp/'


WITH (recommended for supercomputer):

extract_var_and_wr_csv('./tmp/', './csv/output.csv', row)
tmp_dir = './tmp/'

3. Load Required Modules on Talipa

Run these commands inside the HPC terminal:

module load python/3.10
module load hdf5
module load netcdf

4. Create Python Virtual Environment (HPC-safe)

Run:

python3 -m venv tempo_env
source tempo_env/bin/activate


Then install dependencies:

pip install requests zstandard netCDF4 pandas joblib


(If zstandard fails, use:)

pip install --no-binary :all: zstandard

5. Running the Script

Activate the environment:

source tempo_env/bin/activate


Ensure the directories exist:

mkdir -p tmp
mkdir -p csv


Run the script:

python tempo_read_write.py


The script will:

Log in to NASA Earthdata

Download each .nc file listed in tempo_rows.txt

Extract variables into csv/output.csv

Delete .nc files after extraction

6. CSV Output Format

The CSV will contain:

granule_id
original_row
time_start
time_end
product
location
split
granuleSize
vertical_column_troposphere
eff_cloud_fraction
solar_zenith_angle
viewing_zenith_angle
surface_pressure
terrain_height
main_data_quality_flag
ground_pixel_quality_flag
fit_rms_residual
amf_troposphere


Each row corresponds to one TEMPO granule.

7. Notes for HPC Use
✔ No GUI needed

Runs fully in terminal.

✔ Safe for temporary storage

All .nc files are deleted after extraction.

✔ Good for batch jobs

You can submit using Slurm:

Example tempo_job.slurm:

#!/bin/bash
#SBATCH -J tempo
#SBATCH -o tempo.out
#SBATCH -e tempo.err
#SBATCH -t 04:00:00
#SBATCH -N 1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

source tempo_env/bin/activate
python tempo_read_write.py


Submit:

sbatch tempo_job.slurm

8. Troubleshooting
❗ AUTHENTICATION FAILS (Bad Authentication)

Check secure.txt

NASA Earthdata password must be updated every 90 days

Ensure account has accepted the EULA for TEMPO dataset

❗ CSV is empty

Make sure tmp/ and csv/ are used consistently

Ensure URLs in tempo_rows.txt are valid

❗ netCDF4 import errors

Load modules:

module load netcdf
module load hdf5
