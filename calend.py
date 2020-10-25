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

SCOPES = ['https://www.googleapis.com/auth/calendar']

def printRequiredOptionText(text):
	print("No {} given, needs {} to operate.".format(text, text))

def createDate(day, month, year, hour, minute, second=0, startDate=None):

	date = datetime.datetime.now()
	
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

	if(date < datetime.datetime.now() and date.day != datetime.datetime.now().day and year is None):
		date = date.replace(year=date.year+1)

	if(not startDate is None and date < startDate and date + datetime.timedelta(days=1) > startDate):
		date = date + datetime.timedelta(days=1)

	return date


@click.group()
@click.pass_context
def main(ctx):
	creds = None
	ctx.obj = {}

	if os.path.exists('calendarTool/token.pickle'):
		with open('calendarTool/token.pickle', 'rb') as token:
			creds = pickle.load(token)
		ctx.obj["service"] = build('calendar', 'v3', credentials=creds)

	elif((not ctx.invoked_subcommand == "init") and (not ctx.invoked_subcommand == "uninstall")):
		print("Credentials not initialised, please run init.")
		ctx.exit(0)


@main.command(help="Initialize the command line tool with appropriate credentials")
@click.argument("credentialdir") #help="The credential file obtained from the Google Calendar API")
def init(credentialdir):
	flow = InstalledAppFlow.from_client_secrets_file(
		credentialdir, SCOPES)
	creds = flow.run_local_server(port=0)

	with open('calendarTool/token.pickle', 'wb') as token:
		pickle.dump(creds, token)

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
def add(ctx, name, start_hour, end_hour, start_minute, end_minute, date, month, day, fortnightly, repeat, weekly, daily, filename):

	date_day = None

	day = day.lower()

	if(not weekly is None and not daily is None):
		print("\'daily\' option can't be used with the \'weekly\' options")
		ctx.exit(0)

	if(not fortnightly is None and not weekly is None):
		print("\'fortnightly\' option can't be used with the \'weekly\' options")
		ctx.exit(0)

	if(not fortnightly is None and not repeat is None):
		print("\'fortnightly\' option can't be used with the \'repeat\' options")
		ctx.exit(0)

	if(date is None):
		if(day == "today"):
			date_day = datetime.datetime.today().day
		elif(day == "tomorrow"):
			date_day = (datetime.datetime.today() + datetime.timedelta(days=1)).day
	else:
		date_day = date

	rec = []
	if(not weekly is None):
			rec = ['RRULE:FREQ=WEEKLY;COUNT={}'.format(weekly)]
	if(not daily is None):
		rec = ['RRULE:FREQ=DAILY;COUNT={}'.format(daily)]

	maxIter = 1
	freq = 0

	if(not fortnightly is None):
		maxIter = fortnightly
		freq = 14

	if(not repeat is None):
		maxIter = repeat[1]
		freq = repeat[0]

	fnIter = 0

	while(fnIter < maxIter):
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
			with open(filename) as file:
				for f in file.read().splitlines():
					line = f.split(" ")

					start = createDate(date_day, month, None, int(line[1][0:2]), int(line[1][2:4])) + datetime.timedelta(days=freq * fnIter)
					event = {
					  'summary': line[0],
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

@main.command(help="Uninstall the command line tool")
def uninstall():
	subprocess.run(["/usr/local/bin/calendarTool/uninstall.sh"])

# TODO : Delete

if __name__=="__main__":
	main()