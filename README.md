# mapshader
![Test Suite Status](https://github.com/makepath/mapshader/workflows/Python%20Test%20Suite/badge.svg)
--------

Simple Python GIS Web Services

```bash
pip install mapshader
```

#### Setup Mapshader Conda Environment
```bash
conda create -n mapshader python=3.8
conda activate mapshader
git clone git@github.com:makepath/mapshader.git
cd mapshader
pip install -e .
```

#### Run Tests
```bash
conda activate mapshader
pytest mapshader/tests -sv
```

#### Run Flask Server
```bash
conda activate mapshader
python mapshader/flask_app.py

>>> * Serving Flask app "flask_app" (lazy loading)
>>> * Environment: production
>>>   WARNING: This is a development server. Do not use it in a production deployment.
>>>   Use a production WSGI server instead.
>>> * Debug mode: on
>>> * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
>>> * Restarting with stat
```
