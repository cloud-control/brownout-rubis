Brownout RUBiS
==============

Brownout is a software engineering paradigm to make cloud services more robust to capacity shortages. It requires the developer to mark a part of the response as optional and only serve it with a probability given by a dynamic parameter, called the _dimmer_. A controller monitors the response time of the service and adjusts the dimmer, so as to keep the application responsive. Details can be found in [this](http://www8.cs.umu.se/~cklein/publications/icse2014-preprint.pdf) article.

This repository contains the source code of the brownout version of [RUBiS](http://rubis.ow2.org/), an e-commerce website prototype, mimicking eBay. RUBiS is a popular benchmark choice in cloud computing research.

Usage
-----

**NOTE**: We are currently working on making deployment easier.

Each branch contains a tier (`rubis-web-tier`, `rubis-db-tier`). Ensure you have [Docker](https://get.docker.com/) installed on your system.

1. **Build** Docker images:

        for tier in web db; do
            git clone -b rubis-$tier-tier --depth 1 https://github.com/cloud-control/brownout-rubis.git brownout-rubis-$tier-tier
            (cd brownout-rubis-$tier-tier; docker build -t rubis-$tier-tier .)
        done

2. **Run** the Docker containers (type each command in a separate terminal):

        docker run --rm -ti --name rubis-db-tier-0 rubis-db-tier
        docker run --rm -ti --name rubis-web-tier-0 --link rubis-db-tier-0:mysql --publish 80:80 rubis-web-tier

   The database tier might take 60 seconds to start, since it downloads the database dump on startal.

3. **Test** if everything works: Open [this link](http://localhost/PHP/RandomItem.php); if you see the RUBiS logo and some items, then everything works fine.

4. **Shutdown**: The code is meant to be stateless, so kill with fire!

        for tier in web db; do
            docker rm -f rubis-$tier-tier-0
        done

Contact
-------

For questions or comments, please contact Cristian Klein <cklein@cs.umu.se>.
