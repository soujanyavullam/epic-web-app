# Create a new directory for the layer
mkdir -p ~/lambda_layer
cd ~/lambda_layer

# Create the Python package directory structure
mkdir -p python

# Download numpy wheel using pip
pip download numpy==1.24.3 --only-binary=:all: --platform manylinux2014_x86_64 --python-version 39 --implementation cp --abi cp39 -d .

# The wheel file should now be in the current directory
# Install it into our package directory
pip install numpy==1.24.3 --target python/ --no-deps --only-binary=:all: --platform manylinux2014_x86_64 --python-version 39 --implementation cp --abi cp39

# Create the layer zip
zip -r numpy-layer.zip python/

# Create the Lambda layer
aws lambda publish-layer-version \
    --layer-name numpy-layer \
    --description "Numpy layer for Python 3.9" \
    --zip-file fileb://numpy-layer.zip \
    --compatible-runtimes python3.9
