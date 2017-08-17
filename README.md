Brownout RUBiS
==============

Brownout is a software engineering paradigm to make cloud services more robust to capacity shortages. It requires the developer to mark a part of the response as optional and only serve it with a probability given by a dynamic parameter, called the _dimmer_. A controller monitors the response time of the service and adjusts the dimmer, so as to keep the application responsive. Details can be found in [this](http://www8.cs.umu.se/~cklein/publications/icse2014-preprint.pdf) article.

This repository contains the source code of the brownout version of [RUBiS](http://rubis.ow2.org/), an e-commerce website prototype, mimicking eBay. RUBiS is a popular benchmark choice in cloud computing research.

Usage
-----

Each branch contains a tier (`rubis-web-tier`, `rubis-db-tier`, `rubis-control-tier`). Ensure you have [Docker](https://get.docker.com/) installed on your system.

1. **Checkout** the repository with submodule:

        git clone --depth=1 --recursive git@github.com:cloud-control/brownout-rubis.git

2. **Run** experiments

        cd brownout-rubis
        ./start-experiment.sh

3. **Test** if everything works: Open [this link](http://localhost/PHP/RandomItem.php); if you see the RUBiS logo and some items, then everything works fine.

4. **Shutdown**: The code is meant to be stateless, so kill with fire!

        for tier in control web db; do
            docker rm -f rubis-$tier-tier-0
        done

Advanced Usage
--------------

You may use the [`DOCKER_HOST`](https://stackoverflow.com/questions/25234792/what-does-the-docker-host-variable-do) environment variable to deploy the whole experiment on a different machine.

Contact
-------

For questions or comments, please contact Cristian Klein <cklein@cs.umu.se>.
