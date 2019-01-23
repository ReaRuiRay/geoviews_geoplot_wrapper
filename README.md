# geoviews_geoplot_wrapper
## Introduction
This is a plotting wrapper for multi-value plotting in geoviews (https://github.com/pyviz/geoviews)

Geoviews can use bokeh as the renderer, however it currently lacks the ability to show more than one data variable in the hover information (vdims can't be set to more than one variable). As a work-around, we can use holoviews instead and use geoviews for basemaps. We need to use Mercator projeciton in Holoviews so that there is no problem when use holoviews X geoviews. 

Also, unlike matplotlib, Geoviews and Holoviews only accept orthogonal longitude and latitude grids (say, 1-D lon & lat instead of 2-D ones). This is problematic especially for geographical data, where we have a different lon & lat for each data point. Hereby, an interpolation is needed. gv_plot() takes care about all of the regridding using a fast but approximate algorithm.

## Inputs and Outputs
`gv_instance = gv_plot(data, reso, color_var, cmap)`

#### data (dataset)
An xarray dataset with coordinates named `lon` and `lat`. The coordinates and the data variables share the same shape

#### reso (number)
The resolution (unit: meter) in the final plotting. I suggest the resolution close to the input's data resolution. You can tune this to be coarser to make things faster. 

#### color_var (string)
The name of data variable as the colored background. 

#### cmap (string)
The colormap used in plotting. 

#### return gv_instance (geoviews instance)
The return is a geoviews Image instance and can be modified if like. 
If used as `gv_plot(data, reso, color_var, cmap)`, the figure will be plotted directly in Jupyer notebook. 

## Examples for Jupyer Notebook
``` python
import sys
sys.path.append('/location/the/py/file/is/')
from gv_image_plot import gv_image_plot
#import importlib
#importlib.reload(sys.modules['gv_image_plot'])
import geoviews as gv
instance = gv_image_plot(cloud_set, 20000, 'CloudCeiling', 'Blues_r').redim.range(CloudCeiling = (0,4000))
instance * gv.tile_sources.Wikipedia
```
![Output figure](https://github.com/loopal/geoviews_geoplot_wrapper/blob/master/example.png)

## Other Tools
Several methods can be useful for other applications such as the regridding functions (no interpolation, just use nearest neighbor). 

#### regrid_regular(data, lon, lat, reso=0.01)
`data`, `lon`, `lat` are numpy arrays with same shape. `reso` is the output resolution. The domain of output is calculated automatically using the min and max of `lon` and `lat`. The output will be a tuple: `(grid, output_lon, output_lat)`.
