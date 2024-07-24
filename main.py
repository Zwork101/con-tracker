import csv
import requests
from bs4 import BeautifulSoup
import os
import time

roles = {}
previous_events = []
event_counter = 0

url = "https://www.rostercon.com/en/listing-search-results?_rc_people={actor}-en#search-result-rc"
endpoint = os.environ["NOTIFY_ENDPOINT"]
save_file = os.path.join(
	os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "."),
	"events.csv"
)
skip_updates = False

try:
	with open(save_file, newline='') as f:
		previous_events = [*csv.DictReader(f)]
except FileNotFoundError:
	skip_updates = True

with open("actors.csv", newline='') as f:
	next(f)
	reader = csv.reader(f)
	for actor, role, obtained in reader:
		if obtained == "False":
			roles[actor] = role

for actor in roles:
	resp = requests.get(url.format(actor=actor.replace(" ", "-")),
		headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
		})
	soup = BeautifulSoup(resp.text, 'html.parser')
	events = soup.find_all("ul", class_="list-inline row")

	for event in events:
		event_counter += 1
		date = [*event.children][1].text.strip()
		event_name = [*event.children][3].text.strip()
		location = [*event.children][5].text.strip()

		data = {"actor": actor, "date": date,"event": event_name,"location": location}

		if data not in previous_events:
			print(f"{actor} is at {event_name} in {location} on {date}")
			if not skip_updates:
				requests.post(endpoint, data=f"{actor} is at {event_name} in {location} on {date}".encode('utf-8'))
			previous_events.append(data)

	time.sleep(6)

if event_counter < len(previous_events):
	requests.post(endpoint, data=f"Warning: {previous_events} events recorded, only found {event_counter} events")

with open(save_file, "w", newline='') as f:
	writer = csv.DictWriter(f, fieldnames=["actor", "date", "event", "location"])

	writer.writeheader()
	for row in previous_events:
		writer.writerow(row)
