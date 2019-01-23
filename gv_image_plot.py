#Please follow the tutorial of Geoviews on installation at https://github.com/pyviz/geoviews
#Create a new conda environment is highly recommended

import numba
from numba import jit
import geoviews as gv
import geoviews.feature as gf
from holoviews import opts
from holoviews import dim
import holoviews as hv
import xarray as xr
from cartopy import crs
from bokeh.models import HoverTool
import numpy as np
import xarray as xr
from pyproj import Proj, transform
from tqdm import tqdm

import xarray as xr

@jit(nopython=True)
def regrid_regular(data,lon,lat, reso=0.01):
#numpy version, very fast
    region = (np.floor(np.min(lon)), np.floor(np.min(lat)), np.ceil(np.max(lon)), np.ceil(np.max(lat)))
    output_lon = np.arange(region[0],region[2],reso) + reso*0.5
    output_lat = np.arange(region[1],region[3],reso) + reso*0.5
    
    border = (region[0]+reso*0.5, region[1]+reso*0.5, region[2]-reso*0.5, region[3]-reso*0.5)
    
    grid = np.empty((len(output_lat),len(output_lon)))
    grid[:] = np.nan
    #This is an approximate version. If the resolution is too fine, there might be output grids not filled with values. 
    for i in range(1, data.shape[0]-1):
        for j in range(1, data.shape[1]-1):
            if np.isnan(data[i,j]) : 
                continue
                print(i,j)
            xa = max(int(np.round((0.5*(lat[i-1,j]+lat[i,j]) - border[1])/reso)),0)
            xb = min(int(np.round((0.5*(lat[i+1,j]+lat[i,j]) - border[1])/reso))+1, len(output_lat))
            ya = max(int(np.round((0.5*(lon[i,j-1]+lon[i,j]) - border[0])/reso)),0)
            yb = min(int(np.round((0.5*(lon[i,j+1]+lon[i,j]) - border[0])/reso))+1, len(output_lon))
            grid[xa: xb, ya: yb] = data[i,j]
            
    return (grid, output_lon, output_lat)



def regrid_regular_xarray(data, reso):
#accept xarray as input, wrapper of regrid_hrrr_regular()
    lon = data['lon_merc'].values
    lat = data['lat_merc'].values
    
    region = (np.floor(np.min(lon)), np.floor(np.min(lat)), np.ceil(np.max(lon)), np.ceil(np.max(lat)))
    output_lon = np.arange(region[0],region[2],reso) + reso*0.5
    output_lat = np.arange(region[1],region[3],reso) + reso*0.5
    
    border   = (region[0]+reso*0.5, region[1]+reso*0.5, region[2]-reso*0.5, region[3]-reso*0.5)
    
    var_names = list(data.keys())
    
    grid_set = xr.Dataset(coords={'lon_merc': (['lon_merc'], output_lon),\
                               'lat_merc': (['lat_merc'], output_lat)})
    pbar = tqdm(total=len(var_names), desc='Data variable regridding')
    for i in range(0, len(var_names)):
        (grid,garbage1,garbage2) = regrid_regular(data[var_names[i]].values, lon, lat, reso)
        grid_set[var_names[i]] = xr.DataArray(grid,dims=['lat_merc','lon_merc'],name=var_names[i])
        pbar.update(1)
    pbar.close()
                                  
    return grid_set

def gv_plot_merc(data_regrid, color_var, cmap):
    gv.extension('bokeh')

    #resample to lower resolution for performance
    # lower_reso_ratio = 1
    # data_regrid = data_regrid.isel(lon = list(range(0,len(hrrr_output['lon']), lower_reso_ratio)), lat=list(range(0, len(hrrr_output['lat']), lower_reso_ratio)))

    var_names = list(data_regrid.keys())
    
    tooltips=[]
    vdims = [color_var]
    for i in range(0, len(var_names)):
        if ((var_names[i] == 'lat')| (var_names[i] == 'lon')):
            tooltips.insert(0, (var_names[i], '@'+var_names[i]))
        else:
            tooltips.append((var_names[i], '@'+var_names[i]))

        vdims.append(var_names[i])
    if (tooltips[0][0] == 'lat'):
        tooltips.insert(0,tooltips.pop(1))
    
    hover = HoverTool(tooltips=tooltips)

    #This illustrates that the method works!
    data_gv = hv.Image(data_regrid, kdims = ['lon_merc','lat_merc'],\
                       vdims=vdims)                                                     
    data_gv = data_gv.opts(tools=[hover], cmap=cmap,colorbar=True,width=800,height=500)
    
    return data_gv

def gv_image_plot(data, reso, color_var, cmap):
    #If holoviews istances want to work with geoviews, we can only use mercator coords in holoviews, otherwise the coords will be wrong.
    #Holoviews & geoviews only accept normal (orthogonal) grids, so we have to regrid
    #data should a xarray dataset, containing the different key values and coords (lon, lat) of the same shape
    
    #project to geoviews' Mercator lon & lat
    fx, fy = transform(Proj(init='epsg:4326'), Proj(init='epsg:3857'), data['lon'].values, data['lat'].values)
    
    dims = [data['lon'].dims[0], data['lon'].dims[1]]
    x_xr = xr.DataArray(fx,dims=dims,name='lon_merc')
    y_xr = xr.DataArray(fy,dims=dims,name='lat_merc')
    data['lon_merc'] = x_xr
    data['lat_merc'] = y_xr
    data = data.reset_coords(['lon', 'lat']).set_coords(['lon_merc', 'lat_merc'])
    
    #regrid to normal (orthogonal) grids
    data_regrid= regrid_regular_xarray(data,reso)
    
    #plot the regridded data using geoviews
    return gv_plot_merc(data_regrid, color_var, cmap) 