#!/bin/sh
exec /usr/bin/ssh -o StrictHostKeyChecking=no -i /tmp/id_rsa_deployment "$@"