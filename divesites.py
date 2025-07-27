import requests

url = "https://world-scuba-diving-sites-api.p.rapidapi.com/divesites/gps"

# حددنا نطاق بحث بمقدار +/-1 درجة تقريبًا
lat = 27.251671
lng = 33.818291

querystring = {
    "southWestLat": str(lat - 1),
    "northEastLat": str(lat + 1),
    "southWestLng": str(lng - 1),
    "northEastLng": str(lng + 1)
}

headers = {
    "x-rapidapi-key": "096b4db3bamshb42112c4e637e73p1d76c5jsna5257d6ba5f5",
    "x-rapidapi-host": "world-scuba-diving-sites-api.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
