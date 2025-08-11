# Create a new directory for the layer
mkdir -p ~/lambda_layer
cd ~/lambda_layer

# Create a virtual environment with Python 3.9
/opt/homebrew/opt/python@3.9/bin/python3.9 -m venv venv
source venv/bin/activate

# Create the Python package directory structure
mkdir -p python

# Install numpy into the python directory
pip install numpy==1.24.3 --target python/

# Create the layer zip
zip -r numpy-layer.zip python/

# Create the Lambda layer
aws lambda publish-layer-version \
    --layer-name numpy-layer \
    --description "Numpy layer for Python 3.9" \
    --zip-file fileb://numpy-layer.zip \
    --compatible-runtimes python3.9
