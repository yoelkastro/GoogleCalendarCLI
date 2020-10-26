#!/usr/bin/env python3

from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import click
import os
import subprocess

# The scopes of the calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']


# Create a new datetime object with the given parameters. Any parameter can be left as None to default to the value in datetime.datetime.now().

# day: The day of the date
# month: The month of the date
# year: The year of the date. Will increment by one if the provided date is earlier than today.
# hour: The hour of the date
# minute: The minute of the date
# second: The second of the date. 0 by default
# startDate: Only used if the return value will be the end date of an event. Used to make sure the ending time isn't before the starting time.

def createDate(day, month, year, hour, minute, second=0, startDate=None):

	# Get the current datetime
	date = datetime.datetime.now()
	
	# Replace the values of the datetime with desired values if they have been provided.
	if(not day is None):
		date = date.replace(day=day)
	if(not month is None):
		date = date.replace(month=month)
	if(not year is None):
		date = date.replace(year=year)
	if(not hour is None):
		date = date.replace(hour=hour)

	date = date.replace(minute=minute)
	date = date.replace(second=second)

	# If the given date is in the past, increment the year by one if the year wasn't explicitly set
	if(date < datetime.datetime.now() and date.day != datetime.datetime.now().day and year is None):
		date = date.replace(year=date.year+1)

	# If the ending time of the event is before the starting time, move the ending date to the next day
	if(not startDate is None and date < startDate and date + datetime.timedelta(days=1) > startDate):
		date = date + datetime.timedelta(days=1)

	return date


@click.group()
@click.pass_context


# Main command. Authenticates API credentials before calling other commands.

def main(ctx):
	creds = None
	ctx.obj = {}

	if os.path.exists('/usr/local/bin/calendarTool/token.pickle'):
		with open('/usr/local/bin/calendarTool/token.pickle', 'rb') as token:
			creds = pickle.load(token)
		ctx.obj["service"] = build('calendar', 'v3', credentials=creds)

	elif((not ctx.invoked_subcommand == "init") and (not ctx.invoked_subcommand == "uninstall")):
		print("Credentials not initialised, please run init.")
		ctx.exit(0)
# End main

@main.command(help="Initialize the command line tool with appropriate credentials")
@click.argument("credentialdir")

# Initialization command, has to be called after installation. Requires API credentials for setup.

def init(credentialdir):
	flow = InstalledAppFlow.from_client_secrets_file(
		credentialdir, SCOPES)
	creds = flow.run_local_server(port=0)

	with open('/usr/local/bin/calendarTool/token.pickle', 'wb') as token:
		pickle.dump(creds, token)
# End init

@main.command(help="Add a new calendar event")
@click.option("--name", "-n", default="Untitled", help="The name of the calendar event")

@click.option("--start_hour", "-s", default=0, type=int, help="The starting hour of the calendar event")
@click.option("--end_hour", "-e", default=23, type=int, help="The ending hour of the calendar event")
@click.option("--start_minute", "-sm", default=0, type=int, help="The starting minute of the calendar event")
@click.option("--end_minute", "-em", default=0, type=int, help="The ending minute of the calendar event")

@click.option("--date", "-dt", type=int, help="The date of the calendar event")
@click.option("--month", "-m", type=int, help="The value of the calendar event, represented as an integer")
@click.option("--day", "-d", default="today", help="The relative day of the calendar event. Can be TODAY or TOMORROW")

@click.option("--fortnightly", "-fnly", type=int, help="Repeats the event every two weeks the given number of times, takes an integer value")
@click.option("--repeat", "-r", nargs=2, type=int, help="Repeats the event on the given frequency in days the given number of times")

@click.option("--weekly", "-wly", type=int, help="Creates a weekly recurring event repeating the given number of times")
@click.option("--daily", "-dly", type=int, help="Creates a daily recurring event repeating the given number of times")

@click.option("--filename", "-f", help="Creates events based on each line of the given file. Each line must be in the format \"EVENTNAME XXXX YYYY\", where X and Y are the start and end times in military time")
@click.pass_context

# Adds a new calendar event.

def add(ctx, name, start_hour, end_hour, start_minute, end_minute, date, month, day, fortnightly, repeat, weekly, daily, filename):

	# The day for the starting time of the generated event
	date_day = None

	day = day.lower()

	# Make sure conflicting options aren't used together
	if(not weekly is None and not daily is None):
		print("\'daily\' option can't be used with the \'weekly\' options")
		ctx.exit(0)

	if(not fortnightly is None and not weekly is None):
		print("\'fortnightly\' option can't be used with the \'weekly\' options")
		ctx.exit(0)

	if(not fortnightly is None and not repeat == ()):
		print("\'fortnightly\' option can't be used with the \'repeat\' options")
		ctx.exit(0)

	# Setup the day of the event. Defaults to TODAY
	if(date is None):
		if(day == "today"):
			date_day = datetime.datetime.today().day
		elif(day == "tomorrow"):
			date_day = (datetime.datetime.today() + datetime.timedelta(days=1)).day
	else:
		date_day = date

	# Get the rules for recurring events, if the event is recurring
	rec = []
	if(not weekly is None):
			rec = ['RRULE:FREQ=WEEKLY;COUNT={}'.format(weekly)]
	if(not daily is None):
		rec = ['RRULE:FREQ=DAILY;COUNT={}'.format(daily)]

	# The maximum number of repeats of the event. Repeating event are different from recurring events in that recurring events are a function supported by the API while repeating events is just creating the same event on a different day.
	maxIter = 1
	# The frequency of the repeats in days
	freq = 0

	# If repeating fortnightly, set the frequency to 14 days (2 weeks)
	if(not fortnightly is None):
		maxIter = fortnightly
		freq = 14

	# If repeating, set the values to the ones given
	if(not repeat == ()):
		maxIter = repeat[1]
		freq = repeat[0]

	# Iterator
	fnIter = 0

	while(fnIter < maxIter):
		# If the event isn't being obtained from a file, generate one event
		if(filename is None):

			event = {
			  'summary': name,
			  'location': '',
			  'description': '',
			  'start': {
			    'dateTime': (createDate(date_day, month, None, start_hour, start_minute) + datetime.timedelta(days=freq * fnIter)).isoformat(),
			    'timeZone': 'Europe/London',
			  },
			  'end': {
			    'dateTime': (createDate(date_day, month, None, end_hour, end_minute) + datetime.timedelta(days=freq * fnIter)).isoformat(),
			    'timeZone': 'Europe/London',
			  },
			  'recurrence': rec,
			  'attendees': [
			  ],
			  'reminders': {
			    'useDefault': False,
			    'overrides': [],
			  },
			}

			ctx.obj["service"].events().insert(calendarId="primary", body=event).execute()

		else:
		# If the events are being generated from a file, iterate over each line
			with open(filename) as file:
				# TO DO: Fix issue with multiple word event names
				for f in file.read().splitlines():
					line = f.split(" ")

					start = createDate(date_day, month, None, int(line[1][0:2]), int(line[1][2:4])) + datetime.timedelta(days=freq * fnIter)
					event = {
					  'summary': line[0].replace("_", " "),
					  'location': '',
					  'description': '',
					  'start': {
					    'dateTime': start.isoformat(),
					    'timeZone': 'Europe/London',
					  },
					  'end': {
					    'dateTime': (createDate(date_day, month, None, int(line[2][0:2]), int(line[2][2:4]), startDate=start) + datetime.timedelta(days=freq * fnIter)).isoformat(),
					    'timeZone': 'Europe/London',
					  },
					  'recurrence': rec,
					  'attendees': [
					  ],
					  'reminders': {
					    'useDefault': False,
					    'overrides': [],
					  },
					}

					ctx.obj["service"].events().insert(calendarId="primary", body=event).execute()

		fnIter = fnIter + 1

@main.command()
@click.option("--name", "-n", help="Delete all events with the given name.")
@click.pass_context
def delete(ctx, name):
	page_token = None
	while True:
		events = ctx.obj["service"].events().list(calendarId='primary', pageToken=page_token).execute()
		for event in events['items']:
			if(event["summary"] == name):
				ctx.obj["service"].events().delete(calendarId='primary', eventId=event["id"]).execute()
		page_token = events.get('nextPageToken')
		if not page_token:
			break

@main.command(help="Uninstall the command line tool")
def uninstall():
	subprocess.run(["/usr/local/bin/calendarTool/uninstall.sh"])

if __name__=="__main__":
	main()