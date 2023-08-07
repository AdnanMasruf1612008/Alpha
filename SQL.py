import sqlite3
import os
from datetime import datetime, timedelta

#------------------------INSERT------------------------------
def insert_data(jwt, expiration, file_name, pdf_file_path, doc_file_path, UID, Flag):
  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()

  print("Insert from SQL:", jwt, expiration, file_name, pdf_file_path, doc_file_path);
  
  # Create a table
  cursor.execute('CREATE TABLE IF NOT EXISTS users (table_id INTEGER PRIMARY KEY, jwt TEXT, expiration DATETIME, file_name TEXT, pdf_file_path TEXT, doc_file_path TEXT, UID TEXT, Flag INTEGER)')

  # Insert data into the table
  cursor.execute('INSERT INTO users (jwt, expiration, file_name, pdf_file_path, doc_file_path, UID, Flag) VALUES (?, ?, ?, ?, ?, ?, ?)', (jwt, expiration, file_name, pdf_file_path, doc_file_path, UID, Flag,))

  
  conn.commit()
  # print("TABLE AFTER INSERTION")
  # # Query the table
  # cursor.execute('SELECT * FROM users')
  # rows = cursor.fetchall()
  # for row in rows:
  #   print(row) 

  cursor.close()
  conn.close()

#------------------------DELETE------------------------------
def delete_data():
  # Get the current date and time
  current_datetime = datetime.now()
  print("CURRENT:",current_datetime)

  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()

  # Fetch the file_path of each deleted row
  cursor.execute('SELECT pdf_file_path, doc_file_path,UID FROM users WHERE expiration < ?',   (current_datetime,))
  rows = cursor.fetchall()

  print("ROWS:",rows)

  for row in rows:
    pdf = row[0]
    doc = row[1]
    uid = row[2]
    # print("ROW[0]:", pdf)

# Check if the file exists and remove them if they do
    if os.path.exists(pdf):
      os.remove(pdf)

    if os.path.exists(doc):
      os.remove(doc)

    if uid:
      update_cursor = conn.cursor()
      update_cursor.execute('UPDATE users SET jwt=null, expiration = null, pdf_file_path = null, doc_file_path = null, file_name = null, Flag = 0 WHERE UID = ?', (uid,))
      update_cursor.close()

  # Commit the changes and close the connection
  conn.commit()

  # Query the table
  print("TABLE AFTER UPDATE")
  cursor.execute('SELECT * FROM users')
  rows2 = cursor.fetchall()
  for row2 in rows2:
    print(row2) 

  cursor.close()
  conn.close()

def verify_token(jwt_token):
  print ("Inside verify token")
  conn = sqlite3.connect('database.db')  # Replace 'your_database.db' with your actual database file name
  cursor = conn.cursor()
  print ("created cursor")
  print ("JWT Token:",jwt_token)
  # Execute a query to check if the JWT token exists in the database
  cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE jwt = ?)", (jwt_token,))
    
  result = cursor.fetchone()[0]  # Fetch the result of the query
  print ("result:",result)
  cursor.close()
  conn.close()
  return result


def file_path(jwt_token):
  conn = sqlite3.connect(
    'database.db'
  )  # Replace 'your_database.db' with your actual database file name
  cursor = conn.cursor()

  # Execute a query to check if the JWT token exists in the database
  cursor.execute("SELECT pdf_file_path,doc_file_path,file_name FROM users WHERE jwt = ?",
                 (jwt_token, ))

  rows = cursor.fetchall()

  cursor.close()
  conn.close()
  return rows


if __name__ == '__main__':
  pass

