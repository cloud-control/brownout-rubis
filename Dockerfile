FROM ubuntu:16.04
MAINTAINER Cristian Klein <cristiklein@gmail.com>

RUN \
    sed -i s/archive.ubuntu.com/se.archive.ubuntu.com/g /etc/apt/sources.list

RUN \
    apt-get update \
    && apt-get -y install \
        automake \
        build-essential \
        libbz2-dev \
        libtool \
        libpcre3-dev \
        pkg-config \
        python-dev \
        python-numpy \
        zlib1g-dev

COPY autogen.sh configure.ac distribute.sh.in COPYING /usr/src/lighttpd/
COPY doc/config/conf.d/Makefile.am /usr/src/lighttpd/doc/config/conf.d/
COPY doc/config/Makefile.am /usr/src/lighttpd/doc/config/
COPY doc/config/vhosts.d/Makefile.am /usr/src/lighttpd/doc/config/vhosts.d/
COPY doc/initscripts/Makefile.am /usr/src/lighttpd/doc/initscripts/
COPY doc/Makefile.am /usr/src/lighttpd/doc/
COPY doc/outdated/Makefile.am /usr/src/lighttpd/doc/outdated/
COPY doc/scripts/Makefile.am /usr/src/lighttpd/doc/scripts/
COPY doc/systemd/Makefile.am /usr/src/lighttpd/doc/systemd/
COPY Makefile.am /usr/src/lighttpd/./
COPY src/Makefile.am src/server.c /usr/src/lighttpd/src/
COPY tests/docroot/123/Makefile.am /usr/src/lighttpd/tests/docroot/123/
COPY tests/docroot/Makefile.am /usr/src/lighttpd/tests/docroot/
COPY tests/docroot/www/expire/Makefile.am /usr/src/lighttpd/tests/docroot/www/expire/
COPY tests/docroot/www/go/Makefile.am /usr/src/lighttpd/tests/docroot/www/go/
COPY tests/docroot/www/indexfile/Makefile.am /usr/src/lighttpd/tests/docroot/www/indexfile/
COPY tests/docroot/www/Makefile.am /usr/src/lighttpd/tests/docroot/www/
COPY tests/Makefile.am /usr/src/lighttpd/tests/
COPY m4/ax_python_devel.m4 /usr/src/lighttpd/m4/
RUN \
    cd /usr/src/lighttpd; \
    ./autogen.sh; \
    ./configure

COPY doc/ /usr/src/lighttpd/doc/
COPY src/ /usr/src/lighttpd/src/
RUN \
    cd /usr/src/lighttpd; \
    make -j8

COPY lighttpd-brownout-test.conf start-lbb.sh /usr/src/lighttpd/

COPY brownout-lb-simulator /usr/src/lighttpd/brownout-lb-simulator/

WORKDIR /usr/src/lighttpd
CMD ./start-lbb.sh
