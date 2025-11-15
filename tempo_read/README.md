TEMPO NO₂ – Data Download and Preprocessing

This repository contains a utility script (tempo_read_write.py) designed for working with TEMPO Level-2 NO₂ granules on HPC clusters such as Talipa.
The script:

Logs in to NASA Earthdata (URS)

Downloads a list of TEMPO NO₂ Level-2 NetCDF granules

Extracts key variables from each file

Appends the extracted data into a single CSV

Deletes NetCDF files after processing to save disk space

Getting Started
1. Directory Layout

Create your working directory on Talipa:

mkdir -p ~/tempo/{tmp,csv}
cd ~/tempo


Place the following files inside ~/tempo:

tempo_read_write.py

tempo_rows.txt

secure.txt

tempo_rows.txt

Contains one TEMPO NetCDF URL per line:

https://data.asdc.earthdata.nasa.gov/.../TEMPO_NO2_L2_V03_20240301.nc
https://data.asdc.earthdata.nasa.gov/.../TEMPO_NO2_L2_V03_20240301_2.nc

secure.txt

Stores Earthdata login credentials (never commit this to Git):

username=YOUR_EARTHDATA_USERNAME
password=YOUR_EARTHDATA_PASSWORD

2. Adjust Paths in the Script (Linux)

Update paths in tempo_read_write.py:

Old (Windows-style)
download_dir = '/tmp/'
extract_var_and_wr_csv('C:/tmp/', 'C:/csv/output.csv', row)

New (Talipa-friendly)
download_dir = './tmp/'
extract_var_and_wr_csv('./tmp/', './csv/output.csv', row)


Also update the cleanup helper:

tmp_dir = './tmp/'


This ensures all files stay inside your ~/tempo folder.

3. Python Environment on Talipa

Load required system modules:

module load python/3.10
module load hdf5
module load netcdf


Create and activate a virtual environment:

cd ~/tempo
python3 -m venv tempo_env
source tempo_env/bin/activate


Install required packages:

pip install requests zstandard netCDF4 pandas joblib


If zstandard fails to build:

pip install --no-binary :all: zstandard

Running the Script

From ~/tempo:

source tempo_env/bin/activate
mkdir -p tmp csv
python tempo_read_write.py


The script will:

Log in to Earthdata using credentials in secure.txt

Loop through every URL in tempo_rows.txt

Download each NetCDF granule into ./tmp

Extract metadata + selected variables

Append the outputs into ./csv/output.csv

Delete processed .nc files

Output

The primary output file:

./csv/output.csv


Each row corresponds to one TEMPO granule and contains:

granule_id

original_row (URL)

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
