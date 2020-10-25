from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import click
import os

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
@click.option("--credentialdir", "-cd")
@click.pass_context
def main(ctx, credentialdir):
	creds = None
	ctx.obj = {}

	if os.path.exists('calendarTool/token.pickle'):
		with open('calendarTool/token.pickle', 'rb') as token:
			creds = pickle.load(token)
		ctx.obj["service"] = build('calendar', 'v3', credentials=creds)

	elif(not ctx.invoked_subcommand == "init"):
		print("Credentials not initialised, please run init.")
		ctx.exit(0)


@main.command()
@click.argument("credentialdir")
def init(credentialdir):
	flow = InstalledAppFlow.from_client_secrets_file(
		credentialdir, SCOPES)
	creds = flow.run_local_server(port=0)

	os.mkdir("calendarTool")
	with open('calendarTool/token.pickle', 'wb') as token:
		pickle.dump(creds, token)

@main.command()
@click.option("--name", "-n")

@click.option("--start_hour", "-s", type=int)
@click.option("--end_hour", "-e", type=int)
@click.option("--start_minute", "-sm", type=int)
@click.option("--end_minute", "-em", type=int)

@click.option("--date", "-dt", type=int)
@click.option("--month", "-m", type=int)
@click.option("--day", "-d")

@click.option("--weekly", "-wly", type=int)
@click.option("--daily", "-dly", type=int)

@click.option("--filename", "-f")
@click.pass_context
def add(ctx, name, start_hour, end_hour, start_minute, end_minute, date, month, day, weekly, daily, filename):

	date_day = None
	try: 
		if(filename is None):
			if(name is None):
				name = "Untitled"

			if(start_hour is None):
				start_hour = 0

			if(end_hour is None):
				end_hour = 23

			if(start_minute is None):
				start_minute = 0

			if(end_minute is None):
				end_minute = 0

	except ValueError:
		print("Integer value expected for date values, aborting.")
		ctx.exit(0)

	if(date is None and day is None):
		day = "today"
	elif(not day is None):
		day = day.lower()

	if(not day is None and (not date is None or not month is None)):
		print("\'day\' option can't be used with the \'date\' or \'month\' options")
		ctx.exit(0)

	if(not weekly is None and not daily is None):
		print("\'daily\' option can't be used with the \'weekly\' options")
		ctx.exit(0)

	if(not day is None):
		if(day == "today"):
			date_day = datetime.datetime.today().day
		elif(day == "tomorrow"):
			date_day = (datetime.datetime.today() + datetime.timedelta(days=1)).day
	else:
		date_day = date

	rec = []

	if(filename is None):
		if(not weekly is None):
			rec = ['RRULE:FREQ=WEEKLY;COUNT={}'.format(weekly)]
		if(not daily is None):
			rec = ['RRULE:FREQ=DAILY;COUNT={}'.format(daily)]

		event = {
		  'summary': name,
		  'location': '',
		  'description': '',
		  'start': {
		    'dateTime': createDate(date_day, month, None, start_hour, start_minute).isoformat(),
		    'timeZone': 'Europe/London',
		  },
		  'end': {
		    'dateTime': createDate(date_day, month, None, end_hour, end_minute).isoformat(),
		    'timeZone': 'Europe/London',
		  },
		  'recurrence': rec,
		  'attendees': [
		  ],
		  'reminders': {
		    'useDefault': True,
		    'overrides': [],
		  },
		}

		ctx.obj["service"].events().insert(calendarId="primary", body=event).execute()

	else:
		with open(filename) as file:
			for f in file.read().splitlines():
				line = f.split(" ")

				start = createDate(date_day, month, None, int(line[1][0:2]), int(line[1][2:4]))
				event = {
				  'summary': line[0],
				  'location': '',
				  'description': '',
				  'start': {
				    'dateTime': start.isoformat(),
				    'timeZone': 'Europe/London',
				  },
				  'end': {
				    'dateTime': createDate(date_day, month, None, int(line[2][0:2]), int(line[2][2:4]), startDate=start).isoformat(),
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

# TODO : Delete

if __name__=="__main__":
	main()