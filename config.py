DB = {
    'host': 'localhost',
    'dbname': 'test',
    'user': 'admin',
    'password': 'admin',
    'port': 8086,
    'querys':  [
               'SELECT temp FROM Temp where \"sensor\"=\'smhi\' order by desc limit 1;',
               'select temp from Temp where \"location\"=\'tg_kitchen\' order by desc limit 1;',
               'select temp from Temp where \"location\"=\'tg_verkstad\' order by desc limit 1;',
               'select value from PulseCnt order by desc limit 1;'
               ],
    'log_interval_minutes': 1
}

DB2 = {
    'host': '192.168.0.101',
    'dbname': 'db_sensors',
    'user': 'root',
    'password': 'root',
    'port': 8086,
    'querys': ['select temperatureFROM climate group by * order by desc limit 1;',
               'select humidity, dewpoint FROM climate group by * order by desc limit 1;',
               'select dewpoint FROM climate group by * order by desc limit 1;'
              ]
}

GOOGLE = {
    'credentials': 'Torpgarden-f1098109e149.json',
    'key': '1lK_qpAP7nXOxBu1Nl5oPMKbYJdeecNaP0l8MHCkeJWM',
    'sheet': "tg",
    'scope': ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
}


