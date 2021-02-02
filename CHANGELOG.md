## Mapshader Changelog
-----------

## Version 0.0.5 - 2/2/2021
- added support for grouped / non-grouped discrete colormaps via legend
- added legend endpoints
- added legend config object
- added discrete colormaps for raster (should be moved into datashader later)
- added flask cors rule #35

## Version 0.0.4 - 1/27/2020
- added raster_to_categorical_points transform; added ability to manully instantiate services to support integrations
- added hello message
- fixed raster overview generation
- removed datashader line conversion; fixed raster overviews
- fixed double export
- fixed boundaries service
- added tif to netcdf prep script
- fixed tile render bug
- fixed user config bug
- restrucutred sources and added services classes
- added support for NetCDF-backed dask arrays
- general fixes
- added padding and performance fixes for raster layers

### Version 0.0.3 - 1/20/2020
- Added user configs!

### Version 0.0.2 - 1/19/2020
- Many stability fixes

### Version 0.0.1 - 1/18/2020
- First public release available on GitHub and PyPI.
