## Mapshader Changelog
----------------------

### Version 0.1.1 - 2022-02-17
- Overviews netcdf limited area (#113)
- Added serve cli command to start default flask server (#112)
- Fixed issue with template paths when install mapshader via pip (#111)
- Use dask to generate overviews (#110)
- Support multiple GeoTIFF files (#109)
- Add requirements packages version #104 (#106)
- Overviews (#108)
- Services endpoint (#107)
- Remove duplicated get_data_array_extent function #74 (#105)
- Allow different netcdf version in test_valid_conversion (#103)
- Multithreaded support for multiband multiple NetCDF files (#102)
- Add support for reading multiband tiled netcdf files (#101)
- Run tests on pull request and push to default branch (#98)
- Use yaml.safe_load rather than yaml.load (#96)

### Version 0.1.0 - 2021-10-07
- Fixed mapshader config example (#95)
- Added Geojson support Bokeh Previewer support (#67)
- Added docs publishing action (#91)
- Added sphinx (#76)
- Moved hardcoded html (#89)
- Moved services from sources.py to services.py (#90)
- Updated docstrings (#72)
- Added GeoTIFF to NetCDF CLI command (#78)

### Version 0.0.9 - 2021-05-18
- Fixed package requirements

### Version 0.0.8 - 2021-05-17
- Added mapshader on conda-forge

### Version 0.0.7 - 2021-05-17
- Respecting geometry_field when setting default fields
- Separated render functions into get and renderers
- Added psutils perfomance stats (#69)
- Removed double run and moved unnecessary in loop declaration (#68)
- Added basic CLI and examples command (#80)
- Added flake8 Github Action (#77)
- Added PyPi Publish Github Action (#84)

### Version 0.0.6 - 2021-02-12
- Added support for `mapshader.core.to_raster` function for all sources
- Added support for instaniating MapSource directly with `gpd.GeoDataFrame`

### Version 0.0.5 - 2021-02-02
- Added support for grouped / non-grouped discrete colormaps via legend
- Added legend endpoints
- Added legend config object
- Added discrete colormaps for raster (should be moved into datashader later)
- Added flask cors rule (#35)

### Version 0.0.4 - 2021-01-27
- Added raster_to_categorical_points transform; added ability to manully instantiate services to support integrations
- Added hello message
- Fixed raster overview generation
- Removed datashader line conversion; fixed raster overviews
- Fixed double export
- Fixed boundaries service
- Added tif to netcdf prep script
- Fixed tile render bug
- Fixed user config bug
- Restrucutred sources and added services classes
- Added support for NetCDF-backed dask arrays
- General fixes
- Added padding and performance fixes for raster layers

### Version 0.0.3 - 2021-01-20
- Added user configs

### Version 0.0.2 - 2021-01-19
- Many stability fixes

### Version 0.0.1 - 2021-01-18
- First public release available on GitHub and PyPI
