#!/bin/bash
python3 make_db_init.py
sqlite3 movies_ratings.db < db_init.sql
