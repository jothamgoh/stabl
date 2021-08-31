#!/bin/bash
source venv/bin/activate
while true; do
    flask db init; flask db migrate; flask db upgrade; flask populate_data; flask db upgrade
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo Upgrade command failed, retrying in 5 secs...
    sleep 5
done
exec gunicorn -b :5000 --worker-tmp-dir /dev/shm --workers=2 --threads=3 --worker-class=gthread --access-logfile - --error-logfile - stabl:app