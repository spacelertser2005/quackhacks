🚀 TEMPO NO₂ NetCDF → CSV Extractor

Automated Downloader + Parser + Cleaner for TEMPO Level-2 Products

This program downloads TEMPO Level-2 NO₂ NetCDF granules, extracts selected science variables and metadata, writes them into a CSV file, and automatically removes the heavy .nc files to save storage (ideal for HPC clusters with storage limits).

Compatible with Talipa Supercomputer, Linux HPC clusters, and local Windows/macOS machines.

📌 Features
✅ 1. Automatic Login to NASA Earthdata

Uses credentials stored in secure.txt to authenticate and download restricted TEMPO data.

✅ 2. Bulk Download from List

Reads a text file (tempo_rows.txt) containing URLs of TEMPO .nc granules (one per line), then downloads each file into /tmp/.

✅ 3. Complete NetCDF Variable Extraction

Finds variables across:

root group

sub-groups

nested groups

Extracts metadata + core scientific variables including:

vertical_column_troposphere

eff_cloud_fraction

solar_zenith_angle

viewing_zenith_angle

surface_pressure

terrain_height

main_data_quality_flag

ground_pixel_quality_flag

amf_troposphere

fit_rms_residual

Each value is flattened → masked values removed → returns first valid scalar.

✅ 4. Appends to a Single CSV File

Outputs a clean dataset with metadata:

Column	Description
granule_id	File name
original_row	Source download URL
time_start / time_end	Observation timestamps
product	tempo
location	e.g., la
split	e.g., train
granuleSize	File size in bytes
…science variables…	Extracted values
✅ 5. Automatic Cleanup

After each row is processed:

deletes every .nc file in /tmp/

prevents storage overflows in cluster environments

🚀 Ideal for

Machine Learning pipelines

Big-data preprocessing

Hackathons / competitions

NASA Air Quality research

Large-scale TEMPO ingestion on HPC clusters

📁 Required Files

Place these three files in the same folder:

1. tempo_read_write.py

The script (the code you provided).

2. tempo_rows.txt

List of TEMPO NetCDF URLs:

https://data.asdc.earthdata.nasa.gov/.../TEMPO_NO2_L2_V03_20240301.nc
https://data.asdc.earthdata.nasa.gov/.../TEMPO_NO2_L2_V03_20240302.nc
...

3. secure.txt

Your credentials (DO NOT COMMIT TO GIT):

username=YOUR_EMAIL
password=YOUR_PASSWORD

🛠 Installation
Install Python Dependencies
pip install requests zstandard netCDF4 pandas joblib


On Linux HPC systems you may need:

module load python/3.10
module load netcdf

▶️ How to Run
Step 1 — Prepare your input files

Ensure:

tempo_read_write.py
tempo_rows.txt
secure.txt


are in the same directory.

Step 2 — Run the script
python tempo_read_write.py

Output

CSV file will be created at:

C:/csv/output.csv


(or whatever path you set)

Download location

NetCDF files are temporarily stored at:

/tmp/


They will be deleted automatically.

📦 Output CSV Example
granule_id,original_row,time_start,time_end,product,location,split,granuleSize,vertical_column_troposphere,eff_cloud_fraction,solar_zenith_angle,viewing_zenith_angle,surface_pressure,terrain_height,main_data_quality_flag,ground_pixel_quality_flag,fit_rms_residual,amf_troposphere
TEMPO_NO2_L2_20240301.nc,https://.../20240301.nc,2024-03-01T12:00Z,2024-03-01T12:05Z,tempo,la,train,7343201,2.31e15,0.04,21.2,15.7,820.1,150.0,0,0,0.00021,0.95

📚 Code Structure
Function	Purpose
loadFileS3()	Login → Download each file → Extract → Clean
extract_var_and_wr_csv()	Open .nc → search groups → extract variables → write CSV row
find_var()	Find variable in any NetCDF group level
get_scalar()	Return clean numeric scalar
os_remove()	Delete downloaded .nc files
⚠️ Notes & Limitations

NASA servers sometimes throttle; automatic retries may be added later.

The program extracts one value per variable (first valid scalar), not full arrays.

Paths beginning with C:/ assume Windows; adjust if running on HPC/Linux.

🧩 Extending the Script

You can easily modify to:

extract full arrays instead of scalars

save each granule into separate CSV files

merge with CAMS, GEOS-CF, or GFS data

parallelize downloads via joblib
