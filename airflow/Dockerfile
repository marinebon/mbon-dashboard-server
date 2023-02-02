FROM apache/airflow:2.1.3
USER root

# update curl so we can use --fail-with-body option in curl v7.76.0+
# TODO: is libcurl4 a required package too?
RUN apt-get update && \
    apt-get install --yes --no-install-recommends wget build-essential && \
    wget https://curl.se/download/curl-7.78.0.tar.gz && \
    tar -xvf curl-7.78.0.tar.gz && cd curl-7.78.0 && \
    ./configure --with-gnutls && make && make install
