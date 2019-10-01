FROM python:3.6-slim

# Install dev tools
RUN apt-get update && apt-get install -y \
    git

# Copy pyvims dev branch
RUN git clone -b dev https://github.com/seignovert/pyvims.git /pyvims

WORKDIR /pyvims

# Install pyvims library
RUN pip install --no-cache --upgrade pip \
    && pip install --no-cache -rrequirements.txt notebook \
    && python setup.py install

WORKDIR /

# Clean up
RUN apt-get update -y \
    && apt-get remove -y --purge \
    git \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /pyvims

# Check build success
RUN python -c "from pyvims import VIMS"

# Add user for repo2docker
RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid 1000 \
    nbuser

USER nbuser

ENV HOME /home/nbuser

WORKDIR $HOME

# Copy notebooks
COPY --chown=nbuser:nbuser notebooks/ $HOME/.

# Set VIMS_DATA env variable
ENV VIMS_DATA $HOME/data
RUN mkdir -p $VIMS_DATA

EXPOSE 8888
CMD jupyter notebook $HOME/playground.ipynb --ip 0.0.0.0