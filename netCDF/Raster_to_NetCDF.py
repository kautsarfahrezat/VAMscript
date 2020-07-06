#!/usr/bin/env python
# Based on Rich Signell's answer on StackExchange: https://gis.stackexchange.com/a/70487

import numpy as np
import datetime as dt
import os
import gdal
import netCDF4
import re

ds = gdal.Open(r'/Users/bennyistanto/Temp/CHIRPS/SPI/Month1D1/*.tif')
a = ds.ReadAsArray()
nlat,nlon = np.shape(a)

b = ds.GetGeoTransform() #bbox, interval
lon = np.arange(nlon)*b[1]+b[0]
lat = np.arange(nlat)*b[5]+b[3]


basedate = dt.datetime(1980,1,1,0,0,0)

# create NetCDF file
nco = netCDF4.Dataset('time_series.nc','w',clobber=True)

# chunking is optional, but can improve access a lot: 
# (see: http://www.unidata.ucar.edu/blogs/developer/entry/chunking_data_choosing_shapes)
chunk_lon=16
chunk_lat=16
chunk_time=12

# create dimensions, variables and attributes:
nco.createDimension('lon',nlon)
nco.createDimension('lat',nlat)
nco.createDimension('time',None)
timeo = nco.createVariable('time','f4',('time'))
timeo.units = 'days since 1980-1-1 00:00:00'
timeo.standard_name = 'time'

lono = nco.createVariable('lon','f4',('lon'))
lono.units = 'degrees_east'
lono.standard_name = 'longitude'

lato = nco.createVariable('lat','f4',('lat'))
lato.units = 'degrees_north'
lato.standard_name = 'latitude'

# create container variable for CRS: lon/lat WGS84 datum
crso = nco.createVariable('crs','i4')
csro.long_name = 'Lon/Lat Coords in WGS84'
crso.grid_mapping_name='latitude_longitude'
crso.longitude_of_prime_meridian = 0.0
crso.semi_major_axis = 6378137.0
crso.inverse_flattening = 298.257223563

# create short integer variable for precipitation data, with chunking
pcpo = nco.createVariable('pcp', 'i2',  ('time', 'lat', 'lon'), 
   zlib=True,chunksizes=[chunk_time,chunk_lat,chunk_lon],fill_value=-9999)
pcpo.units = 'mm'
pcpo.scale_factor = 0.01
pcpo.add_offset = 0.00
pcpo.long_name = '"Climate Hazards group InfraRed Precipitation with Stations"'
pcpo.standard_name = 'precipitation'
pcpo.grid_mapping = 'crs'
pcpo.set_auto_maskandscale(False)

nco.Conventions='CF-1.6'

#write lon,lat
lono[:]=lon
lato[:]=lat

pat = re.compile('rbb_cli_chirps-v2.0.[0-9]{4}\.[0-9]{2}')
itime=0

#step through data, writing time and data to NetCDF
for root, dirs, files in os.walk(r'/Users/bennyistanto/Temp/CHIRPS/SPI/Month1D1/'):
    dirs.sort()
    files.sort()
    for f in files:
        if re.match(pat,f):
            # read the time values by parsing the filename
            year=int(f[8:12])
            mon=int(f[13:15])
            date=dt.datetime(year,mon,1,0,0,0)
            print(date)
            dtime=(date-basedate).total_seconds()/86400.
            timeo[itime]=dtime
           # precipitation
            pcp_path = os.path.join(root,f)
            print(pcp_path)
            pcp=gdal.Open(pcp_path)
            a=pcp.ReadAsArray()  #data
            pcpo[itime,:,:]=a
            itime=itime+1

nco.close()