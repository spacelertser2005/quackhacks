TEMPO NO₂ NetCDF → CSV Extractor

Automated downloader, parser, and cleaner for TEMPO Level-2 NO₂ NetCDF files

This program:

Logs into NASA Earthdata using your credentials

Downloads TEMPO Level-2 NO₂ NetCDF granules from a list of URLs

Extracts selected metadata and science variables

Appends everything into a single CSV file

Deletes the .nc files afterward to save storage (useful on HPC clusters)

Features

Automatic Earthdata login using secure.txt

Bulk download of TEMPO NetCDF granules from tempo_rows.txt

Variable extraction from root and nested NetCDF groups

Single CSV output with one row per granule

Automatic cleanup of .nc files in /tmp/

Extracted Fields

Each granule produces one row with:

Metadata

granule_id – NetCDF file name

original_row – Original download URL

time_start, time_end – Time coverage attributes from the file

product – Hard-coded to tempo

location – Hard-coded to la (can be changed)

split – Hard-coded to train (for ML pipelines)

granuleSize – File size in bytes

Science variables (scalar summaries)
The script looks through the root group and all subgroups for each variable, flattens the data, drops masked / NaN values, and returns the first valid scalar:

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

Required Files

Place these files in the same directory as the script:

1. tempo_read_write.py

Your main Python script (the code you have now).

2. tempo_rows.txt

A text file containing one TEMPO NetCDF URL per line, for example:

https://data.asdc.earthdata.nasa.gov/.../TEMPO_NO2_L2_V03_20240301.nc

https://data.asdc.earthdata.nasa.gov/.../TEMPO_NO2_L2_V03_20240301_2.nc

3. secure.txt

Your NASA Earthdata login (do not commit this to Git):

username=YOUR_EMAIL_HERE
password=YOUR_EARTHDATA_PASSWORD

Installation

Install the required Python packages:

pip install requests zstandard netCDF4 pandas joblib


On an HPC system you may also need to load modules, for example:

module load python/3.10
module load netcdf

How It Works
1. Authentication and Download (loadFileS3)

Reads secure.txt into a secure dictionary.

Logs into https://urs.earthdata.nasa.gov using requests.post.

Reads all lines from tempo_rows.txt.

For each URL (row):

Downloads the .nc file into /tmp/.

Calls extract_var_and_wr_csv('C:/tmp/', 'C:/csv/output.csv', row) (you can adjust these paths).

Calls os_remove() to delete .nc files after processing.

Note: Right now download_dir is /tmp/ but extract_var_and_wr_csv is pointed at C:/tmp/.
If you’re only working on Linux or only on Windows, make sure these match.

2. NetCDF Parsing and CSV Writing (extract_var_and_wr_csv)

Looks for .nc files in the given file_dir.

Defines the CSV header:

granule_id, original_row, time_start, time_end,
product, location, split, granuleSize,
vertical_column_troposphere, eff_cloud_fraction,
solar_zenith_angle, viewing_zenith_angle,
surface_pressure, terrain_height,
main_data_quality_flag, ground_pixel_quality_flag,
fit_rms_residual, amf_troposphere

Ensures the output directory for output_csv_path exists.

For each NetCDF file:

Opens it with Dataset(file_path, 'r').

Reads global attributes: time_coverage_start, time_coverage_end.

Computes granuleSize via os.path.getsize.

Uses get_scalar() to safely extract each science variable.

Appends a new row to the CSV file.

If the CSV does not exist or is empty, it writes the header first.

3. Finding Variables in Nested Groups (find_var and get_scalar)

find_var(nc, name):

Checks nc.variables at the root.

Looks through each group in nc.groups.

Also checks one level deeper in subgroups.

get_scalar(nc, name):

Uses find_var to locate the variable.

Reads all data, flattens it.

If it’s a masked array, it calls .compressed().

Returns the first finite value (v == v filters out NaN).

Returns an empty string if nothing valid is found.

4. Cleanup (os_remove)

Looks at /tmp/ for all files ending in .nc.

Deletes each one with os.remove.

Logs success or “does not exist” for each filename.

This keeps your temporary directory from filling up on a cluster.

Running the Script

Make sure you have:

tempo_read_write.py

tempo_rows.txt

secure.txt

Run:

python tempo_read_write.py


After it runs successfully, your CSV will be at:

C:/csv/output.csv (based on the current script), or

Whatever path you set in extract_var_and_wr_csv.

Sample CSV Row
granule_id,original_row,time_start,time_end,product,location,split,granuleSize,vertical_column_troposphere,eff_cloud_fraction,solar_zenith_angle,viewing_zenith_angle,surface_pressure,terrain_height,main_data_quality_flag,ground_pixel_quality_flag,fit_rms_residual,amf_troposphere
TEMPO_NO2_L2_20240301.nc,https://.../TEMPO_NO2_L2_V03_20240301.nc,2024-03-01T12:00:00Z,2024-03-01T12:05:00Z,tempo,la,train,7343201,2.31e15
