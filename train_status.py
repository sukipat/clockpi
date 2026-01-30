import time
import requests
from datetime import datetime
from google.transit import gtfs_realtime_pb2
from google.protobuf.message import DecodeError


# Uses gtfs_realtime_bindings to fetch GTFS feed based on URL
# Params:
# 	FEED_URL (String): Web URL for GTFS Endpoint
# 
# Return (tuple):
#	"feed": FeedMessage | None
#		GTFS feed type
#   "error": None | "network" | "server"
# 		String based on requests error code
def _fetch_feed(FEED_URL):
	try:
		response = requests.get(FEED_URL, timeout=10)
		response.raise_for_status()
		
		feed = gtfs_realtime_pb2.FeedMessage()
		feed.ParseFromString(response.content)

		return {
            "feed": feed,
            "error": None
        }

	except DecodeError:
		return {"feed": None, "error": "server"}

	except requests.exceptions.Timeout:
		return {"feed": None, "error": "network"}

	except requests.exceptions.ConnectionError:
		return {"feed": None, "error": "network"}
		
	except requests.exceptions.RequestException:
		return {"feed": None, "error": "server"}

# Uses GTFS feed, target station, target trains, and number of trains
# Returns list of train_count number of trains in either direction
# Params:
# 	feed (gtfs_feed): GTFS feed type from fetch_feed
#	station (String): Station from MTA protobuf without N/S suffix
#	trains (List of Strings): Route names to check for
#	train_count (Int): Number of arrivals to provide in each direction
# 
# Return (list):
#	uptown_arrivals (List of tuples): route_id (String) and minutes_away (Int)
#	downtown_arrivals (List of tuples): route_id (String) and minutes_away (Int)
def _get_arrivals(feed, station, trains, train_count):
	now = time.time()
	uptown_arrivals = []
	downtown_arrivals = []

	for entity in feed.entity:
		if not entity.HasField("trip_update"):
			continue

		trip = entity.trip_update.trip
		route_id = trip.route_id

		if route_id not in trains:
			continue

		for stu in entity.trip_update.stop_time_update:
			if not stu.stop_id.startswith(station):
				continue

			arrival_time = None
			
			# if stu.arrival and stu.arrival.time:
			arrival_time = stu.arrival.time
			# elif stu.departure and stu.departure.time:
			# 	arrival_time = stu.departure.time

			if arrival_time:
				delta_seconds = arrival_time - now
				
				if delta_seconds > 0:
					minutes_away = int(delta_seconds/60)
					if (stu.stop_id == (station + "N")):
						uptown_arrivals.append((route_id, minutes_away))
					else:
						downtown_arrivals.append((route_id, minutes_away))

	uptown_arrivals.sort(key=lambda x: x[1])
	downtown_arrivals.sort(key=lambda x: x[1])

	return [uptown_arrivals[:train_count],downtown_arrivals[:train_count]]

# Testing function to print trains from a list of route, min tuples
# Params:
#	arrivals (List of tuples): List of (route_id, minutes_away) tuples to print
def _print_arrivals(arrivals):
	for route, mins in arrivals:
		if mins == 0:
			mins = "<1"
		print(f"{route} train in {mins} min")

# General purpose external function to return a dict of uptown trains, downtown trains, and any error codes
# Params:
# 	URLS (List of Strings): List of GTFS endpoints strings to pass into fetch_feed
#	station (String): Station from MTA protobuf without N/S suffix
#	trains (List of Strings): Route names to check for
#	train_count (Int): Number of arrivals to provide in each direction
# 
# Return (tuple):
#	"uptown" (List of tuples): route_id (String) and minutes_away (Int)
#	"downtown" (List of tuples): route_id (String) and minutes_away (Int)
#	"error" (String): None or String to print to represent error
def get_arriving_trains(URLS, station, trains, train_count):
	feeds = []
	error_code = None

	for url in URLS:
		feed = _fetch_feed(url)
		if feed["error"]:
			e = feed["error"]
			if e == "network":
				error_code = "Network connection issue,\nsome trains may not be displayed"
				continue
			else:
				error_code = "Issue fetching feed,\nsome trains may not be displayed"
				continue
		feeds.append(feed)

	arrivals = []
	for feed in feeds:
		arrival = _get_arrivals(feed["feed"],station, trains, train_count)
		arrivals.append(arrival)


	uptown_arrivals = []
	downtown_arrivals = []
	for arrival in arrivals:
		uptown_arrivals = uptown_arrivals + arrival[0]
		downtown_arrivals = downtown_arrivals + arrival[1]

	uptown_arrivals.sort(key=lambda x: x[1])
	downtown_arrivals.sort(key=lambda x: x[1])

	return {"uptown": uptown_arrivals[:train_count], "downtown": downtown_arrivals[:train_count], "error": error_code}

def main():
	print("Starting ABCD arrival monitor (125 St)")

	AC_FEED_URL="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"
	BD_FEED_URL="https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"
	FEED_URLS = [AC_FEED_URL, BD_FEED_URL]

	TARGET_ROUTES = {"A", "C", "B", "D"}
	TARGET_STOP = "A15"

	NUM_TRAINS = 4
	
	arriving_trains = get_arriving_trains(FEED_URLS,TARGET_STOP,TARGET_ROUTES,NUM_TRAINS)

	if arriving_trains["error"]:
		print(arriving_trains["error"])

	uptown_trains = arriving_trains["uptown"]
	downtown_trains = arriving_trains["downtown"]

	print("\n" + "Uptown Arrivals:")
	if not uptown_trains:
		print("No arrivals soon...")
	else:
		_print_arrivals(uptown_trains)

	print("\n" + "Downtown Arrivals:")
	if not downtown_trains:
		print("No arrivals soon...")
	else:
		_print_arrivals(downtown_trains)

if __name__ == "__main__":
	main()
