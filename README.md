# mapshader
![Test Suite Status](https://github.com/makepath/mapshader/workflows/Python%20Test%20Suite/badge.svg)
--------

Simple Python GIS Web Services

```bash
pip install mapshader (coming soon...)
```

```bash
conda install -c conda-forge mapshader (coming soon...)
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
```
