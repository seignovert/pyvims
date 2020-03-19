FROM python:3.6-slim

RUN pip install https://github.com/seignovert/pyvims/archive/dev.zip && \
    python -c 'from pyvims import VIMS'

WORKDIR /pyvims

ENTRYPOINT [ "python" ]