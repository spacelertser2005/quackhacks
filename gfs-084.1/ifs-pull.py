
# In[1]:


import os
import time
import pickle
from datetime import datetime, timedelta, date  # <-- added date
import tarfile
import numpy as np
import pandas as pd
import requests
import pygrib
import zstandard as zstd

from joblib import Parallel, delayed, parallel_backend


# In[2]:


feats = [
    (11,  'Wind speed (gust):m s**-1 (instant):regular_ll:surface:level 0'),
    (402, 'Surface pressure:Pa (instant):regular_ll:surface:level 0'),
    (406, 'Volumetric soil moisture content:Proportion (instant):regular_ll:depthBelowLandLayer:levels 0.0-0.1 m'),
    (415, '2 metre temperature:K (instant):regular_ll:heightAboveGround:level 2 m'),
    (416, '2 metre specific humidity:kg kg**-1 (instant):regular_ll:heightAboveGround:level 2 m'),
    (418, '2 metre relative humidity:% (instant):regular_ll:heightAboveGround:level 2 m'),
    (419, 'Apparent temperature:K (instant):regular_ll:heightAboveGround:level 2 m'),
    (420, '10 metre U wind component:m s**-1 (instant):regular_ll:heightAboveGround:level 10 m'),
    (421, '10 metre V wind component:m s**-1 (instant):regular_ll:heightAboveGround:level 10 m'),
    (436, 'Cloud water:kg m**-2 (instant):regular_ll:atmosphereSingleLayer:level 0 considered as a single layer'),
    (437, 'Relative humidity:% (instant):regular_ll:atmosphereSingleLayer:level 0 considered as a single layer'),
    (438, 'Total ozone:DU (instant):regular_ll:atmosphereSingleLayer:level 0 considered as a single layer'),
]


# In[3]:


cities = {
    "USA": (
        (-125.0, -66.0),  # longitude range
        (24.0,   50.0),   # latitude range
    )
}


# In[4]:


def processGFS(file, d):
    """
    file : local GFS GRIB2 file
    d    : integer padding in grid cells around the box

    Returns a list of tuples:
      (variable_string, spot_name,
       ((lat_min, lat_max), (lon_min, lon_max)),
       subarray_with_padding (float32),
       mean_value_over_core_box)
    """
    p = pygrib.open(file)
    lat, lon = p[1].latlons()  # 2D arrays

    spots = {}
    for city, ((lonmin, lonmax), (latmin, latmax)) in cities.items():
        # Find grid indices INSIDE the requested lat/lon box
        mask = (
            (lat >= latmin) & (lat <= latmax) &
            (lon >= lonmin) & (lon <= lonmax)
        )

        if not mask.any():
            # No grid points in this box
            continue

        idx = np.where(mask)
        xmin = idx[0].min()
        xmax = idx[0].max()
        ymin = idx[1].min()
        ymax = idx[1].max()

        spots[city] = ((xmin, xmax), (ymin, ymax))

    data = []

    for e in p:
        if any(z in str(e) for i, z in feats):
            arr = e.values
            assert arr.shape == lat.shape

            for spot, ((xmin, xmax), (ymin, ymax)) in spots.items():
                # padded slice
                x0 = max(xmin - d, 0)
                x1 = min(xmax + 1 + d, lat.shape[0])
                y0 = max(ymin - d, 0)
                y1 = min(ymax + 1 + d, lat.shape[1])

                lat_box = lat[x0:x1, y0:y1]
                lon_box = lon[x0:x1, y0:y1]
                arr_box = arr[x0:x1, y0:y1].astype(np.float32)

                core = arr[xmin:xmax + 1, ymin:ymax + 1]
                mean_val = float(core.mean())

                data.append(
                    (
                        str(e),                        # description string
                        spot,                          # "USA"
                        ((lat_box.min(), lat_box.max()),
                         (lon_box.min(), lon_box.max())),
                        arr_box,                       # padded subarray
                        mean_val                       # mean over core box
                    )
                )

    p.close()
    return data


# In[5]:


def pullGFS(files):
    results = []

    # Base for GFS 0.25° (d084001)
    dspath = 'https://data.rda.ucar.edu/d084001/'
    save_dir = '/tmp/'
        
    zc = zstd.ZstdCompressor(level=9)

    processed_dir = 'inference/gfs-5'
    os.makedirs(processed_dir, exist_ok=True)

    print('Downloading {} gfs files'.format(len(files)))

    for file in files:
        start = time.time()

        # we only want the filename part for local disk
        filename = os.path.basename(file)

        # Where the compressed result will live
        out_path = os.path.join(processed_dir, filename + '.zst')
        processed_file = out_path

        # Skip if already processed
        if os.path.exists(processed_file):
            print(f"Skipping already processed file: {filename}")
            continue

        # Temporary raw GRIB file location
        outfile = os.path.join(save_dir, filename)

        for i in range(10):
            try:
                # Build full URL using the new base
                full_url = dspath + file.lstrip('/')  # ensure no double slashes

                print('Downloading', full_url)
                with requests.get(full_url, allow_redirects=True, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    with open(outfile, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
            
                s = os.path.getsize(outfile)

                # Your existing GFS → dict extractor
                data = processGFS(outfile, 5)

                # Delete raw GRIB to save space
                os.remove(outfile)

                # Compress the pickle with zstd
                pkl = pickle.dumps(data)
                compr = zc.compress(pkl)

                with open(out_path, 'wb') as f:
                    f.write(compr)

                results.append({
                    'file': filename,
                    'body': s / 1e6,             # MB
                    'outlen': len(pkl),
                    'outlen-compr': len(compr),
                    'elapsed_time': round(time.time() - start, 1)
                })

                print(f"OK: wrote {out_path}")
                break
        
            except Exception as e:
                print("ERROR:", e)
                time.sleep(i)
                try:
                    os.remove(outfile)
                except:
                    pass

    return results


# In[6]:


def listGFSFiles(dates):
    """
    dates: list of datetime.date or datetime.datetime objects

    Returns list of ds084.1 relative paths like:
      '20240301/20240301/gfs.0p25.2024030100.f000.grib2'
    for hours [0, 6, 12, 18]
    """
    filelist = []
    fwd = 0  # forecast hour

    for t in dates:
        dt = t.strftime('%Y%m%d')
        for hr in [0, 6, 12, 18]:
            filelist.append(
                '{}/{}/gfs.0p25.{}{:02d}.f{:03d}.grib2'.format(
                    dt[:4], dt, dt, hr, fwd
                )
            )
    return filelist


# In[7]:


def march_2024_dates():
    """
    Helper: returns [2024-03-01, ..., 2024-03-31] as datetime.date objects.
    """
    start = date(2024, 3, 1)
    end   = date(2024, 3, 31)
    n_days = (end - start).days + 1
    return [start + timedelta(days=i) for i in range(n_days)]


# In[ ]:


if __name__ == '__main__':
    dates = march_2024_dates()
    files = listGFSFiles(dates)

    print("Num dates:", len(dates),
          "first:", dates[0],
          "last:", dates[-1])
    print("Num GFS files:", len(files))
    print("Example path:", files[0])

    # Number of workers
    N_THREADS = min(4, os.cpu_count() or 1)
    print(f"Using {N_THREADS} parallel workers")

    # Use THREADING backend (avoids Windows + pygrib multiprocess issues)
    with parallel_backend("threading", n_jobs=N_THREADS):
        # Each worker handles a slice of the list: files[i::N_THREADS]
        results_lists = Parallel()(
            delayed(pullGFS)(files[i::N_THREADS])
            for i in range(N_THREADS)
        )

    # Flatten list of lists if you care about the return values
    results = [item for sublist in results_lists for item in sublist]

    print(f"Total files processed: {len(results)}")


# --- March 1 to March 31 date window ---
start = date(2024, 3, 1)
end   = date(2024, 3, 31)

# --- Your condition ---
if start.year <= 2018 and end.year >= 2021:
    os.makedirs('cache', exist_ok=True)

    # Loop through each subdirectory under "inference/"
    for path in os.listdir('inference'):
        full_dir = os.path.join('inference', path)

        # Skip files; only process directories
        if not os.path.isdir(full_dir):
            continue

        # Tar output path
        tar_path = os.path.join('cache', f"{path}.tar")

        print(f"Creating tar: {tar_path}")

        # Create tar archive (uncompressed)
        with tarfile.open(tar_path, "w") as tar:
            for file in os.listdir(full_dir):
                file_path = os.path.join(full_dir, file)
                tar.add(file_path, arcname=file)

        print(f"Done: {tar_path}")
# In[ ]:




