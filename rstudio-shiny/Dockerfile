FROM rocker/geospatial:latest
MAINTAINER "Ben Best" ben@ecoquants.com

# install extra packages 
RUN install2.r --error \
  # for shiny:
  Rcpp \
  httpuv \
  shiny \
  # for app: https://github.com/BenioffOceanInitiative/ships4whales-app/blob/master/shiny_ships/app.R
  dbplyr \
  fs \
  glue \
  gstat \
  here \
  leaflet \
  units \
  RColorBrewer \
  RPostgreSQL \
  RPostgres \
  shinydashboard
  
  # already included: https://tidyverse.tidyverse.org
  #   dplyr
  #   lubridate
  # already included: https://github.com/rocker-org/geospatial
  #   maptools
  #   raster
  #   rgdal
  #   rgeos
  #   sf
  #   sp
  #   tmap
  
# add Shiny, per https://github.com/rocker-org/rocker/issues/235#issuecomment-299036810
RUN export ADD=shiny && bash /etc/cont-init.d/add

# install Shiny apps
#RUN cd /srv && rm -rf shiny-server && \
#    git clone https://github.com/marinebon/iea-ne_apps.git shiny-server
    
