# Some libraries here

#!/usr/bin/env python
import os
import sys
import psycopg2

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gettingstarted.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)




    DATABASE_URL = os.environ['DATABASE_URL']

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    
#Loop through this while! < 1

# Assign I/O pins to input values


# Convert input values to usable data



# PLACEHOLDER


# Store values in local array?


# Upload values to DB.... heroku?



# Clear array

