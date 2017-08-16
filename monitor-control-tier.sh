#!/bin/bash
watch -n1 -- 'curl -v http://localhost/PHP/RandomItem.php -o /dev/null 2>&1 | egrep "(Brownout|Optional)"'
