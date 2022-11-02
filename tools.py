import mysql.connector.pooling
from constants import *
import dotenv
import os


def query(pool, myquery, commit=False, args=None):
    conn = pool.get_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute(myquery, args)
        if commit:
            conn.commit()
        else:
            result = cursor.fetchall()
    except mysql.connector.Error as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
        return result


def filter(msg):
    count = 0
    for word in FILTER:
        if word in msg:
            count+=1
    if count>1:
        return True     # ban
    else:
        return False


def my_name(attributes):
    if len(attributes['args'])>1:
        if attributes['args'][1][0]=='@':    # Slice off @
            attributes['args'][1] = attributes['args'][1][1:]
        return attributes['args'][1]     # The first argument is the name
    else:
        return attributes['author']


def get_header():
    dotenv.load_dotenv(override=True)
    header = {"Client-ID": os.getenv('CLIENTID'), 
                "Authorization":"Bearer {0}".format(os.getenv('ACCESSTOKEN')), 
                "Content-Type":"application/json"}
    return header

def get_header2():
    dotenv.load_dotenv(override=True)
    header = {"Client-ID": os.getenv('CLIENTID'), 
                "Authorization":"Bearer {0}".format(os.getenv('ACCESSTOKEN2')), 
                "Content-Type":"application/json"}
    return header