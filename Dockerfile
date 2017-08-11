FROM mysql:5.5
MAINTAINER Cristian Klein <cristiklein@gmail.com>

RUN apt-get update && apt-get install -y \
    curl \
    xz-utils

COPY *.sh *.sql.gz *.sql /docker-entrypoint-initdb.d/
COPY *.cnf /etc/mysql/conf.d/
ENV MYSQL_RANDOM_ROOT_PASSWORD=yes
ENV MYSQL_DATABASE=rubis
ENV MYSQL_USER=cecchet
ENV MYSQL_PASSWORD=

