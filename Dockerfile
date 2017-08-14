FROM php:5.6-apache
MAINTAINER Cristian Klein <cristiklein@gmail.com>
RUN docker-php-ext-install \
    mysql \
    sockets
RUN echo "output_buffering=4096" >> /usr/local/etc/php/php.ini

# Install controller prerequisites
RUN apt-get update \
    && apt-get install -y \
        python \
        python-numpy

# Support at least 1000 simultaneous connections and silence ServerName warning
COPY mpm_prefork.conf /etc/apache2/mods-available/

# Avoid ServerName warnings
COPY servername.conf /etc/apache2/conf-available/
RUN a2enconf servername

COPY PHP/ /var/www/html/PHP/

CMD /var/www/html/PHP/localController.py & apache2-foreground > /dev/null
