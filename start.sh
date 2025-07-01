#!/usr/bin/env bash

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:$PORT trix.wsgi:application 