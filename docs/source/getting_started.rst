===============
Getting Started
===============
Setup Mapshader Conda Environment
*********************************

.. code-block:: bash

   conda create -n mapshader python=3.8  
   conda activate mapshader  
   git clone git@github.com:makepath/mapshader.git  
   cd mapshader  
   pip install -e .  


Run Tests
*********

.. code-block:: bash

   conda activate mapshader
   pytest mapshader/tests -sv


Run Flask Server
****************

.. code-block:: bash

   conda activate mapshader
   python mapshader/flask_app.py


.. code-block:: bash

   >>> * Serving Flask app "flask_app" (lazy loading)
   >>> * Environment: production
   >>>   WARNING: This is a development server. Do not use it in a production deployment.
   >>>   Use a production WSGI server instead.
   >>> * Debug mode: on
   >>> * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
   >>> * Restarting with stat


Mapshader Config (YAML)
***********************
While mapshader comes with default services to help with testing, users can create their own services
via YAML.

*my_services.yaml*

.. code-block:: yaml

   ---

   metadata:
   version: 1

   sources:
   - name: Elevation
      key: elevation-user
      text: Elevation
      description: Global elevation
      geometry_type: raster
      shade_how: linear
      span: min/max
      raster_interpolate: linear
      xfield: geometry
      yfield: geometry
      filepath: ~/mapshader/mapshader/tests/fixtures/elevation.tif
      transforms:
         - name: squeeze
         args:
            dim: band
         - name: cast
         args:
            dtype: float64
         - name: orient_array
         - name: flip_coords
         args:
            dim: y
         - name: reproject_raster
         args:
            epsg: 3857


This configuration file can then be passed to the flask server upon startup:

.. code-block:: bash

   conda activate mapshader
   python mapshader/flask_app.py -f my_services.yaml


.. code-block:: bash

   >>> * Serving Flask app "flask_app" (lazy loading)
   >>> * Environment: production
   >>>   WARNING: This is a development server. Do not use it in a production deployment.
   >>>   Use a production WSGI server instead.
   >>> * Debug mode: on
   >>> * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
   >>> * Restarting with stat
