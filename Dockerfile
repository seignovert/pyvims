FROM python:3.6-slim

# Install dev libs
RUN apt-get update && apt-get install -y \
    g++ \
    git \
    # GDAL
    libgdal-dev \
    libgdal20 \
    # OpenCV
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    # Python Basemap
    libgeos-dev \
    libgeos-3.7.1 \
    libgeos-c1v5

# Install GDAL for Python
RUN pip install --no-cache --upgrade pip \
    && pip install --no-cache \
    numpy \
    matplotlib \
    notebook \
    Pillow \
    wget \
    && pip install --no-cache \
    gdal==$(gdal-config --version) \
    git+https://github.com/matplotlib/basemap.git \
    pyvims

# Clean up
RUN apt-get update -y \
    && apt-get remove -y --purge \
    g++ \
    git \
    libgdal-dev \
    libgeos-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Check build success
RUN python -c "from pyvims import VIMS"

# Add user for repo2docker
RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid 1000 \
    nbuser

WORKDIR /home/nbuser
USER nbuser

COPY --chown=nbuser:nbuser playground.ipynb .
COPY --chown=nbuser:nbuser pyvims.ipynb .
RUN mkdir -p ~/data ~/kernels

EXPOSE 8888
CMD jupyter notebook ~/playground.ipynb --ip 0.0.0.0