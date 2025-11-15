# TEMPO NO₂ – Data Download and Preprocessing

This repository contains a small utility script, `tempo_read_write.py`, that:

1. Logs in to NASA Earthdata (URS).
2. Downloads a list of TEMPO NO₂ Level-2 NetCDF granules.
3. Extracts a set of key variables from each file.
4. Appends them to a single CSV file.
5. Deletes the NetCDF files to conserve disk space on the cluster.

---

## Getting started

### 1. File layout

Create a working directory on Talipa, for example:

```bash
mkdir -p ~/tempo/{tmp,csv}
cd ~/tempo
Place the following files in ~/tempo:

tempo_read_write.py

tempo_rows.txt

secure.txt

tempo_rows.txt should contain one TEMPO NetCDF URL per line, e.g.:

text
Copy code
https://data.asdc.earthdata.nasa.gov/.../TEMPO_NO2_L2_V03_20240301.nc
https://data.asdc.earthdata.nasa.gov/.../TEMPO_NO2_L2_V03_20240301_2.nc
secure.txt should store NASA Earthdata credentials (this file must not be committed to Git):

text
Copy code
username=YOUR_EARTHDATA_USERNAME
password=YOUR_EARTHDATA_PASSWORD
2. Adjust paths in the script (Linux vs Windows)
On Talipa we use the local folders ./tmp and ./csv instead of Windows drives.

In tempo_read_write.py, update the following lines:

python
Copy code
download_dir = '/tmp/'
...
extract_var_and_wr_csv('C:/tmp/', 'C:/csv/output.csv', row)
Change them to:

python
Copy code
download_dir = './tmp/'
...
extract_var_and_wr_csv('./tmp/', './csv/output.csv', row)
In the helper that deletes files, also set:

python
Copy code
tmp_dir = './tmp/'
This keeps all intermediate files inside the ~/tempo directory.

3. Python environment on Talipa
Load system modules:

bash
Copy code
module load python/3.10
module load hdf5
module load netcdf
Create and activate a virtual environment:

bash
Copy code
cd ~/tempo
python3 -m venv tempo_env
source tempo_env/bin/activate
Install required packages:

bash
Copy code
pip install requests zstandard netCDF4 pandas joblib
If zstandard fails to build wheels on the cluster, use:

bash
Copy code
pip install --no-binary :all: zstandard
Running the script
From ~/tempo with the environment activated:

bash
Copy code
source tempo_env/bin/activate
mkdir -p tmp csv       # no-op if they already exist
python tempo_read_write.py
The script will:

POST credentials in secure.txt to https://urs.earthdata.nasa.gov and obtain cookies.

Loop over each URL in tempo_rows.txt.

Download each NetCDF file into ./tmp.

For each .nc file, extract metadata and selected variables and append a row to ./csv/output.csv.

Delete the processed .nc files from ./tmp.

Output
The main output file is:

text
Copy code
./csv/output.csv
Each row corresponds to one TEMPO granule and contains:

granule_id

original_row (original download URL)

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

Optional: run as a Slurm job
Create a Slurm script, for example tempo_job.slurm:

bash
Copy code
#!/bin/bash
#SBATCH -J tempo
#SBATCH -o tempo.out
#SBATCH -e tempo.err
#SBATCH -t 04:00:00
#SBATCH -N 1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

module load python/3.10
module load hdf5
module load netcdf

cd ~/tempo
source tempo_env/bin/activate
python tempo_read_write.py
Submit with:

bash
Copy code
sbatch tempo_job.slurm
Troubleshooting
Authentication errors (Bad Authentication)

Re-check secure.txt (username and password).

Ensure the Earthdata account has accepted the EULA for the TEMPO product.

Passwords expire periodically; update if needed.

Empty or missing CSV output

Confirm tempo_rows.txt contains valid URLs.

Check that tmp/ and csv/ exist and paths in the script point to ./tmp/ and ./csv/output.csv.

Import errors for netCDF4

Make sure module load netcdf and module load hdf5 were run before activating the environment.

Reinstall netCDF4 if necessary inside the tempo_env environment.

makefile
Copy code
::contentReference[oaicite:0]{index=0}









C
