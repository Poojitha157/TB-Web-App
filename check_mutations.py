import sqlite3

conn = sqlite3.connect("tb_system.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM mutation")
count = cursor.fetchone()[0]

print("Total mutations in database:", count)

conn.close()
