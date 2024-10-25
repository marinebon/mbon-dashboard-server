FROM nginx:stable

# install website from Github
# RUN apt-get update; apt-get --assume-yes install git
# RUN cd /usr/share/nginx && rm -rf html && \
#    git clone https://github.com/mhk-env/mhk-env.github.io.git html

COPY ./nginx.conf /etc/nginx/conf.d/default.conf