import os
from time import sleep
import requests
import smtplib
import numpy as np
import dotenv
import os

dotenv.load_dotenv()

app_mail = os.getenv("app_mail")
password = os.getenv("password")
pers_email = os.getenv("pers_email")

def send_email(letter_body):
    connection = smtplib.SMTP("smtp.gmail.com")
    connection.starttls()  # secure the connection (tls)

    connection.login(user=app_mail, password=password)
    message = f"Subject:ISS is now Visible!\n\n{letter_body}"
    connection.sendmail(from_addr=app_mail, to_addrs=pers_email, msg=message.encode("utf-8"))
    connection.close()

def get_el(iss_lat, iss_lon, city):

    r_earth = 6371000
    iss_alt = float(400000)

    if city == "MILANO":
        obs_lat = float(45.4638878)
        obs_lon = float(9.1897562)
    elif city == "HOME":
        obs_lat = float(45.546032)
        obs_lon = float(9.388413)
    else:
        return False


    def llh_to_ecef(lat, lon, alt):
        lat_rad = np.radians(lat)
        lon_rad = np.radians(lon)
        r = r_earth + alt
        x = r * np.cos(lat_rad) * np.cos(lon_rad)
        y = r * np.cos(lat_rad) * np.sin(lon_rad)
        z = r * np.sin(lat_rad)
        return np.array([x, y, z])

    def elevation_angle(sat_pos, obs_pos):
        vector = sat_pos - obs_pos
        distance = np.linalg.norm(vector)
        vertical = obs_pos / np.linalg.norm(obs_pos)
        cos_theta = np.dot(vector, vertical) / distance
        elevation = np.degrees(np.arcsin(cos_theta))
        return elevation

    pos_obs = llh_to_ecef(obs_lat, obs_lon, 0)
    pos_iss = llh_to_ecef(float(iss_lat), float(iss_lon), iss_alt)

    el = elevation_angle(pos_iss, pos_obs)

    print_el = f"Elevation angle {city}: {el:.2f}°"
    print(print_el)

    return el


while True:
    try:
        sleep(60)  # check every 60 seconds

        print("\n---------------------------------------------------\n")

        # get iss position
        response = requests.get(url="http://api.open-notify.org/iss-now.json")
        response.raise_for_status()
        response_data = response.json()
        iss_latitude = response_data["iss_position"]["latitude"]
        iss_longitude = response_data["iss_position"]["longitude"]

        print_lat_lon = f"\nLatitude: {iss_latitude}, Longitude: {iss_longitude}"
        print(print_lat_lon)

        # get sunrise and sunset time
        params_sunrise = {'lat': iss_latitude, 'lng': iss_longitude}
        response = requests.get(url="https://api.sunrise-sunset.org/json", params=params_sunrise)
        response.raise_for_status()
        response_data = response.json()
        sunrise = response_data["results"]["sunrise"]
        sunset = response_data["results"]["sunset"]
        print_rise_n_set = f"\nSunrise: {sunrise}, Sunset: {sunset}"
        print(print_rise_n_set)

        # reverse geocoding
        headers = {'User-Agent': 'main.py/1.0'}
        params_nominatim = {
            'lat': iss_latitude,
            'lon': iss_longitude,
            'format': 'json'
        }
        response = requests.get("https://nominatim.openstreetmap.org/reverse", headers=headers, params=params_nominatim)
        response.raise_for_status()
        response_data = response.json()
        address = response_data.get("display_name", "Unknown location")
        print_address = f"\nAddress: {address}\n"
        print(print_address)

        # visibility checks
        # milan_el = get_el(iss_latitude, iss_longitude, "MILANO")
        home_el = get_el(iss_latitude, iss_longitude, "HOME")

        # if milan_el > 0:
        #     print("Visible in MILANO sky!")
        #     text_milano = f"ISS is right above MILANO!\n{print_lat_lon}{print_rise_n_set}{print_address}Angle:{milan_el}"
        #     send_email(text_milano)

        if home_el > 0:
            print("Visible in HOME sky!")
            text_home = f"ISS is right above HOME!\n{print_lat_lon}{print_rise_n_set}{print_address}Angle:{home_el}"
            send_email(text_home)
        else:
            print("Not visible")

        # if not milan_el > 0 and not home_el > 0:
        #     print("Not visible")

    except Exception as e:
        print(f"⚠️ Exception: {e}")
        continue
