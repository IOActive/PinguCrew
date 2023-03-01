mongo-schema-export.py --uri mongodb://127.0.0.1:27017/ --database luckycat

mongo-schema-import.py --uri mongodb://127.0.0.1:27017/ --databases luckycat --verbose --delete-col
