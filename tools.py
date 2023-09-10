import mysql.connector.pooling
from constants import *
import dotenv
import os
from bs4 import BeautifulSoup
import pandas
import random
import boto3
import botocore
import threading

access_tokens_lock = threading.Lock()
access_tokens = {}


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
            count += 1
    if count > 1:
        return True  # ban
    else:
        return False


def my_name(attributes):
    if len(attributes["args"]) > 1:
        if attributes["args"][1][0] == "@":  # Slice off @
            attributes["args"][1] = attributes["args"][1][1:]
        return attributes["args"][1]  # The first argument is the name
    else:
        return attributes["author"]


def get_header_user(user_id):
    with access_tokens_lock:
        print(access_tokens)
        if access_tokens.get(user_id):
            print("cache hit")
            user_access_token = access_tokens.get(user_id)
        else:
            print("cache miss")
            client = boto3.client("dynamodb", region_name="us-west-2")
            response = client.get_item(
                Key={
                    "CookieHash": {
                        "S": user_id,
                    }
                },
                TableName="CF-Cookies",
            )
            user_access_token = response["Item"]["AccessToken"]["S"]
            access_tokens[user_id] = user_access_token

    header = {
        "Client-ID": os.getenv("CLIENTID"),
        "Authorization": f"Bearer {user_access_token}",
        "Content-Type": "application/json",
    }
    return header


def get_bot_token():
    client = boto3.client("dynamodb", region_name="us-west-2")
    response = client.get_item(
        Key={
            "CookieHash": {
                "S": "681131749",
            }
        },
        TableName="CF-Cookies",
    )
    user_access_token = response["Item"]["AccessToken"]["S"]
    return user_access_token


def fill_table(csv):
    # csv = numpy.array([[ 0.17899619,  0.33093259,  0.2076353,   0.06130814,],
    #             [ 0.20392888,  0.42653105,  0.33325891,  0.10473969,],
    #             [ "asdfghjklasdfghjklasdfgh",  0.19081956,  0.10119709,  0.09032416,],
    #             [-0.10606583, -0.13680513, -0.13129103, -0.03684349,],
    #             [ 0.20319428,  0.28340985,  0.20994867,  0.11728491,],
    #             [ 0.04396872,  0.23703525,  0.09359683,  0.11486036,],
    #             [ 0.27801304, -0.05769304, -0.06202813,  0.04722761,],])

    soup = BeautifulSoup(open("./S3/template.html"), "html.parser")

    title = csv[0][0]
    header = csv[1]
    body = csv[2:]

    tab_title = soup.find("div", {"id": "tab-title"})
    tab_title.string = title

    page_title = soup.find("div", {"id": "page-title"})
    page_title.string = title

    df = pandas.DataFrame(body, columns=header)
    html = df.to_html(justify="center", escape=False)
    html = html.replace("&", "&amp;")

    soup2 = BeautifulSoup(html, "html.parser")

    for th in soup2.findAll("th"):
        th["class"] = "w-5"

    table = soup2.find("table", {"class": "dataframe"})
    del table["border"]
    table["class"] = "table table-striped text-center"

    div = soup.find("div", {"id": "main-table"})
    div.append(soup2)

    with open("./S3/output1.html", "w", encoding="utf-8") as file:
        file.write(str(soup))


def fill_clips(csv, profile_image_url, offline_image_url, file_name):
    object_content = f'<!DOCTYPE html>\n<html lang="en">\n<head>\n  <title id="tab-title"></title>\n  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1">\n  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet">\n  <link rel="icon" type="image/x-icon" href="{profile_image_url}">\n <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js"></script>\n\n  <link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Kalam&display=swap" rel="stylesheet">\n\n</head>\n<body>\n\n<div class="container-fluid p-0 bg-success text-white text-center" id="div-banner">\n  <div class="d-flex justify-content-center align-items-center w-100 h-100 mask text-white text-center" style="background-color: rgba(0, 0, 0, 0.3);" id="div-mask">\n    <h1 id="page-title" class="display-1" style="font-family: \'Kalam\', cursive;"></h1>\n</div>\n</div>\n\n<div class="container-fluid table-responsive" id="main-table">\n\n</div>\n\n</body>\n</html>\n'
    object_content = object_content.encode()
    soup = BeautifulSoup(object_content, "html.parser")

    title = csv[0][0]
    header = csv[1]
    body = csv[2:]

    tab_title = soup.find("title", {"id": "tab-title"})
    tab_title.string = title

    page_title = soup.find("h1", {"id": "page-title"})
    page_title.string = title

    background = ["bg-primary", "bg-success", "bg-info", "bg-warning", "bg-danger"]
    div_banner = soup.find("div", {"id": "div-banner"})
    div_banner[
        "class"
    ] = f"container-fluid display-1 m-0 p-0 {random.choice(background)}"
    div_banner["style"] = "height: 30vh;"
    if offline_image_url is not None:
        if offline_image_url != "":
            div_banner["class"] = "container-fluid display-1 m-0 p-0 bg-image"
            div_banner[
                "style"
            ] = f"background-image: url('{offline_image_url}'); height: 30vh; background-repeat:no-repeat; background-position:top center;"

    df = pandas.DataFrame(body, columns=header)
    html = df.to_html(justify="center", escape=False)
    html = html.replace("&", "&amp;")

    soup2 = BeautifulSoup(html, "html.parser")

    for th in soup2.findAll("th"):
        th["class"] = "w-5"

    for a in soup2.findAll("a"):
        td = a.parent
        td["class"] = "w-50"

    table = soup2.find("table", {"class": "dataframe"})
    del table["border"]
    table["class"] = "table table-striped text-center"

    div = soup.find("div", {"id": "main-table"})
    div.append(soup2)

    # with open(f"./S3/clips-{file_name}.html", "w", encoding='utf-8') as file:
    #     file.write(str(soup))
    upload_to_s3(f"clips/clips-{file_name}.html", str(soup).encode("utf-8"), False)


# fill_table(None)


def upload_to_s3(path, bytes, retain=False):
    client = boto3.client("s3", region_name="us-west-2")

    if retain:
        tag = "do-not-delete=yes"
    else:
        tag = "do-not-delete=no"

    response = client.put_object(
        ACL="bucket-owner-full-control",
        Body=bytes,
        Bucket="a-poorly-written-bot",
        ContentType="text/html",
        CacheControl="max-age=120",
        Key=path,
        Tagging=tag,
    )

    # print(response)
    return
