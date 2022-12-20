import mysql.connector.pooling
from constants import *
import dotenv
import os
from bs4 import BeautifulSoup
import pandas
import random
import boto3
import botocore


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

# ACCESSTOKEN2 is for the bot
def get_header2():
    dotenv.load_dotenv(override=True)
    header = {"Client-ID": os.getenv('CLIENTID'), 
                "Authorization":"Bearer {0}".format(os.getenv('ACCESSTOKEN2')), 
                "Content-Type":"application/json"}
    return header

# ACCESSTOKEN3 is for the me
def get_header3():
    dotenv.load_dotenv(override=True)
    header = {"Client-ID": os.getenv('CLIENTID'), 
                "Authorization":"Bearer {0}".format(os.getenv('ACCESSTOKEN3')), 
                "Content-Type":"application/json"}
    return header


def fill_table(csv):
    # csv = numpy.array([[ 0.17899619,  0.33093259,  0.2076353,   0.06130814,],
    #             [ 0.20392888,  0.42653105,  0.33325891,  0.10473969,],
    #             [ "asdfghjklasdfghjklasdfgh",  0.19081956,  0.10119709,  0.09032416,],
    #             [-0.10606583, -0.13680513, -0.13129103, -0.03684349,],
    #             [ 0.20319428,  0.28340985,  0.20994867,  0.11728491,],
    #             [ 0.04396872,  0.23703525,  0.09359683,  0.11486036,],
    #             [ 0.27801304, -0.05769304, -0.06202813,  0.04722761,],])

    soup = BeautifulSoup(open('./S3/template.html'), 'html.parser')
    
    title = csv[0][0]
    header = csv[1]
    body = csv[2:]

    tab_title = soup.find("div", {"id": "tab-title"})
    tab_title.string = title

    page_title = soup.find("div", {"id": "page-title"})
    page_title.string = title

    df = pandas.DataFrame(body, columns=header)
    html = df.to_html(justify="center", escape=False)
    html = html.replace('&', '&amp;')
    
    soup2 = BeautifulSoup(html, 'html.parser')

    for th in soup2.findAll("th"):
        th['class'] = "w-5"

    table = soup2.find("table", {"class": "dataframe"})
    del table['border']
    table['class'] = "table table-striped text-center"

    div = soup.find("div", {"id": "main-table"})
    div.append(soup2)

    with open("./S3/output1.html", "w", encoding='utf-8') as file:
        file.write(str(soup))


def fill_clips(csv, offline_image_url, file_name):
    soup = BeautifulSoup(open('./S3/template.html'), 'html.parser')
    
    title = csv[0][0]
    header = csv[1]
    body = csv[2:]

    tab_title = soup.find("title", {"id": "tab-title"})
    tab_title.string = title

    page_title = soup.find("h1", {"id": "page-title"})
    page_title.string = title

    background = ['bg-primary', 'bg-success', 'bg-info', 'bg-warning', 'bg-danger']
    div_banner = soup.find("div", {"id": "div-banner"})
    div_banner['class'] = f"container-fluid display-1 p-5 text-white text-center {random.choice(background)}"
    if offline_image_url is not None:
        if offline_image_url!='':
            div_banner['class'] = "container-fluid display-1 p-5 text-white text-center bg-image"
            div_banner['style'] = f"background-image: url('{offline_image_url}'); height: 30vh; background-repeat:no-repeat; background-position:top center;"

    df = pandas.DataFrame(body, columns=header)
    html = df.to_html(justify="center", escape=False)
    html = html.replace('&', '&amp;')
    
    soup2 = BeautifulSoup(html, 'html.parser')

    for th in soup2.findAll("th"):
        th['class'] = "w-5"

    for a in soup2.findAll("a"):
        td = a.parent
        td['class'] = 'w-50'

    table = soup2.find("table", {"class": "dataframe"})
    del table['border']
    table['class'] = "table table-striped text-center"

    div = soup.find("div", {"id": "main-table"})
    div.append(soup2)

    # with open(f"./S3/clips-{file_name}.html", "w", encoding='utf-8') as file:
    #     file.write(str(soup))
    upload_to_s3(f"clips/clips-{file_name}.html", str(soup).encode('utf-8'), False)

# fill_table(None)

def upload_to_s3(path, bytes, retain=False):
    client = boto3.client('s3', region_name='us-west-2')

    if retain:
        tag = 'do-not-delete=yes'
    else:
        tag = 'do-not-delete=no'

    response = client.put_object(
        ACL='bucket-owner-full-control',
        Body=bytes,
        Bucket='a-poorly-written-bot',
        ContentType='text/html',
        Key=path,
        Tagging=tag
    )

    # print(response)
    return