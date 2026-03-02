import os
from dotenv import load_dotenv


load_dotenv()

ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_TOKEN = os.getenv("ZABBIX_TOKEN")
HOST_GROUP_ID = os.getenv("HOST_GROUP_ID")