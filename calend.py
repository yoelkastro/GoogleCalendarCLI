from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import click

SCOPES = ['https://www.googleapis.com/auth/calendar']

def printRequiredOptionText(text):
	print("No {} given, needs {} to operate.".format(text, text))


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

	with open('token.pickle', 'wb') as token:
		pickle.dump(creds, token)

@main.command()
@click.option("--name", "-n")

@click.option("--start_hour", "-s")
@click.option("--end_hour", "-e")
@click.option("--start_minute", "-sm")
@click.option("--end_minute", "-em")

@click.option("--date", "-dt")
@click.option("--month", "-m")
@click.option("--day", "-d")

@click.option("--filename", "-f")
@click.pass_context
def add(ctx, name, start_hour, end_hour, start_minute, end_minute, date, month, day, filename):
	if(filename is None):
		if(name is None):
			name = "Untitled"

		if(start_hour is None):
			start_hour = 0
		else:
			start_hour = int(start_hour)

		if(end_hour is None):
			end_hour = 24
		else:
			end_hour = int(end_hour)

		if(start_minute is None):
			start_minute = 0
		else:
			start_minute = int(start_minute)

		if(end_minute is None):
			end_minute = 24
		else:
			end_minute = int(end_minute)

	if(date is None and day is None):
		day = "today"
	else:
		day = day.lower()

	if(not day is None and (not date is None or not month is None)):
		print("\'day\' option can't be used with the \'date\' or \'month\' options")
		ctx.exit(0)

	
	

if __name__=="__main__":
	main()