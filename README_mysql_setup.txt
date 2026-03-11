MYSQL INTEGRATION STARTER

Files in this package:
- requirements_mysql.txt
- .env.example
- mysql_config.py
- mysql_client.py
- test_mysql_connection.py
- official_layer_schema.sql

Recommended steps:
1. Install requirements:
   python -m pip install -r requirements_mysql.txt
2. Copy .env.example to .env
3. Edit .env locally and set your actual password there
4. Run:
   python test_mysql_connection.py

Important:
- Do not keep real passwords inside source files
- Rotate the password after sharing it in chat
