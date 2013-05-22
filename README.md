# ercot

A library for interacting with The Electric Reliability Council of Texas
(ERCOT)'s website and data.

All this code is extremely unorganized and is just a series of proof of concepts
at the moment.


wget command:

    wget -q http://www.ercot.com/content/cdr/html/real_time_system_conditions.html \
    -O real_time_system_conditions$(date +\%s).html
