FROM php:5.6-apache
MAINTAINER Cristian Klein <cristiklein@gmail.com>
COPY PHP/ /var/www/html/PHP/
RUN docker-php-ext-install mysql
RUN echo "output_buffering=4096" >> /usr/local/etc/php/php.ini
