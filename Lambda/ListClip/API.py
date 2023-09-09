import requests
import boto3
import botocore
import os
import random
from bs4 import BeautifulSoup
import pandas
import numpy

def get_header_user(user_id):
    client = boto3.client('dynamodb', region_name='us-west-2')
    response = client.get_item(
        Key={
            'CookieHash': {
                'S': user_id,
            }
        },
        TableName='CF-Cookies',
    )
    user_access_token =  response["Item"]['AccessToken']['S']
    
    header = {"Client-ID": os.getenv('CLIENTID'), 
                "Authorization":f"Bearer {user_access_token}", 
                "Content-Type":"application/json"}
    return header


def broadcaster_ID(name, header):
    r = requests.get(url=f"https://api.twitch.tv/helix/users?login={name}", headers=header)
    if r.status_code!=200:
        return None, f'[ERROR]: status code is {str(r.status_code)}'
    data = r.json()
    if len(data['data'])==0:
        return None, "[ERROR]: User not found"
    return data['data'][0], None
    

def get_game_from_id(game_id, header):
    r = requests.get(url=f"https://api.twitch.tv/helix/games?id={game_id}", headers=header)
    if r.status_code!=200:
        return f'[ERROR]: status code is {str(r.status_code)}'
    else:
        data = r.json()
        data = data.get('data')
        if data is not None:
            if len(data)>0:
                return data[0]['name']
        return '-'


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
        CacheControl='max-age=120',
        Key=path,
        Tagging=tag
    )

    # print(response)
    return


def fill_clips(csv, profile_image_url, offline_image_url, file_name):
    # client = boto3.client('s3', region_name='us-west-2')
    # s3_response_object = client.get_object(Bucket='a-poorly-written-bot', Key='template.html')
    # object_content = s3_response_object['Body'].read()
    # print(type(object_content))
    # print(object_content)

    # soup = BeautifulSoup(open('./template.html'), 'html.parser')
    object_content = f'<!DOCTYPE html>\n<html lang="en">\n<head>\n  <title id="tab-title"></title>\n  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1">\n  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet">\n  <link rel="icon" type="image/x-icon" href="{profile_image_url}">\n <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js"></script>\n\n  <link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Kalam&display=swap" rel="stylesheet">\n\n</head>\n<body>\n\n<div class="container-fluid p-0 bg-success text-white text-center" id="div-banner">\n  <div class="d-flex justify-content-center align-items-center w-100 h-100 mask text-white text-center" style="background-color: rgba(0, 0, 0, 0.3);" id="div-mask">\n    <h1 id="page-title" class="display-1" style="font-family: \'Kalam\', cursive;"></h1>\n</div>\n</div>\n\n<div class="container-fluid table-responsive" id="main-table">\n\n</div>\n\n</body>\n</html>\n'
    object_content = object_content.encode()
    soup = BeautifulSoup(object_content, 'html.parser')
    
    title = csv[0][0]
    header = csv[1]
    body = csv[2:]

    tab_title = soup.find("title", {"id": "tab-title"})
    tab_title.string = title

    page_title = soup.find("h1", {"id": "page-title"})
    page_title.string = title

    background = ['bg-primary', 'bg-success', 'bg-info', 'bg-warning', 'bg-danger']
    div_banner = soup.find("div", {"id": "div-banner"})
    div_banner['class'] = f"container-fluid display-1 m-0 p-0 {random.choice(background)}"
    div_banner['style'] = "height: 30vh;"
    if offline_image_url is not None:
        if offline_image_url!='':
            div_banner['class'] = "container-fluid display-1 m-0 p-0 bg-image"
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


def listclip(user, force, max, header):
    limit = 10      # We're only gonna search 10*100 = 1000 clips
    games = {}

    override = False
    # 0 means no override
    if force is not None:
        if force.lower()=='true':
            override = True

    if max is not None:
        if max.isnumeric():
            limit = int(max)
            if limit>5000:
                limit = 5000
            limit//=100
    
    # Get user ID from name
    user, error_message = broadcaster_ID(user, header)
    if not user:      # It's an error message
        return error_message
    id = user['id']
    display_name = user['display_name']
    profile_image_url = user['profile_image_url']
    offline_image_url = user['offline_image_url']

    csv = numpy.array([[f"{display_name}'s Clips", '', '', '', ''], \
        ["Clip", "Game", "Views", "Created At", "Creator Name"]])

    if not override:
        s3 = boto3.resource('s3')
        try:
            s3.Object('a-poorly-written-bot', f'clips/clips-{display_name}.html').load()
        except botocore.exceptions.ClientError as e:
            pass
        else:
            return f"https://apoorlywrittenbot.cc/clips/clips-{display_name}.html"

    # Get top clips
    r = requests.get(url=f"https://api.twitch.tv/helix/clips?broadcaster_id={id}&first=100", headers=header)
    for i in range(limit):
        if r.status_code!=200:
            return f"[ERROR]: status code is not {str(r.status_code)}"
        data = r.json()

        for item in data.get('data'):
            title = item.get('title')
            link = item.get('url')
            creator_name = item.get('creator_name')
            view_count = item.get('view_count')
            created_at = item.get('created_at')
            game_id = item.get('game_id')

            game_name = games.get(game_id)
            if game_name is None:
                game_name = get_game_from_id(game_id, header)
                games[game_id] = game_name
            
            url = f"<a href=\"{link}\" class=\"link-dark\" target=\"_blank\" rel=\"noopener noreferrer\">{title}</a>"

            csv = numpy.append(csv, [[url, game_name, view_count, created_at, creator_name]], axis=0)

        pagination = data.get('pagination').get('cursor')
        if pagination is None or pagination=='':
            break
        # Continue from pagination index
        r = requests.get(url=f"https://api.twitch.tv/helix/clips?broadcaster_id={id}&first=100&after={pagination}", headers=header)

    fill_clips(csv, profile_image_url, offline_image_url, display_name)
    return f"https://apoorlywrittenbot.cc/clips/clips-{display_name}.html"
