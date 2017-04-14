import httplib2     
import os
from subprocess import Popen, PIPE, STDOUT
from shutil import copyfile  
from apscheduler.schedulers.background import BackgroundScheduler   

#from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime
import time
from time import sleep
import commands
import serial


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


'''
'Squid is a caching proxy server which supports almost all popular protocols like 
'HTTP, HTTPS, FTP, etc and lets you cache and filter the traffic on these protocols.
'We use squid to filter the internet traffic. Blocking filtering has to be set in to
'squid.conf file. to do so, we have made two separate squid.conf files for "work" and
'"rest" functionalities; which each one has its own filtering rules. Any user who uses
'this rasbpery pi machine as proxy, his internet data will be filtered based on "work"
'and "rest" rules implemented in squid.conf
'''
srcwork='work/squid.conf'
srcrest='rest/squid.conf'
dest='/etc/squid.conf'

#A global variable for storing the pandora player process when it is called.
pandora_proc = None

def get_credentials():
    """Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials
'''
'If there is a work event in calendar, work function will be called which
'changes the filtering rules and plays music.
'''
def work():   
    global pandora_proc #references the variable that stores the pandora player process
    copyfile(srcwork,dest) #
    
    DEVNULL = open(os.devnull, 'wb') #opens a writable pipe to the /dev/null
    '''
    'opens a seperate shell and calls the pianobar executable.
    'since we don't need the output, it is piped to the /dev/null folder 
    'where it is discarded
    '''
    '''
    'These first two lines open up a serial connection to the arduino and 
    'send it an 'a'. When the arduino recieves the 'a' it turns on the LEDs
    'and sets their color to blue
    '''
    s = serial.Serial('/dev/ttyACM0', 9600, timeout=5)
    s.write("1")
    pandora_proc = Popen(['pianobar'], shell=True, stdin=PIPE, stdout=DEVNULL, stderr=STDOUT)
    fade_in_audio() #calls the function to gradually fade in the pandora volume
    return proc
'''
'After 45 minutes of work, "rest" function will be called which changes the
'filtering rules and terminates the music. 
'''
def rest():   
    global pandora_proc #references the variable that stores the pandora player process
    copyfile(srcrest,dest)
    fade_out_audio() #calls the function to gradually fade out the pandora volume
    pandora_proc.terminate() #kills the pianobar process, which stops the music
    '''
    'These last two lines open up a serial connection to the arduino and 
    'send it a 'b'. When the arduino recieves the 'b' it turns on the LEDs
    'and sets their color to green
    '''
    s = serial.Serial('/dev/ttyACM0', 9600, timeout=5)
    s.write("0")
    

def fade_in_audio():    
    '''
    'This for loop iterates from 50 to 100 in increments of 2.
    'At each increment, a command is sent to set the system volume to variable i%
    'To control the rate at which the audio is faded in, the loop sleeps for 
    '.2 seconds at each iteration.
    '''
    for i in range(50, 100, 2):
        ret = commands.getoutput("amixer set PCM " + str(i) + "%")
        sleep(0.2)

def fade_out_audio():
    '''
    'This for loop iterates from 100 to 50 in increments of -2.
    'At each increment, a command is sent to set the system volume to variable i%
    'To control the rate at which the audio is faded out, the loop sleeps for 
    '.2 seconds at each iteration.
    '''
    for i in range(100, 50, -2):
        ret = commands.getoutput("amixer set PCM " + str(i) + "%")
        sleep(0.2)

def main():
    """Shows basic usage of the Google Calendar API.
    Creates a Google Calendar API service object and outputs a list of the next
    events on the user's calendar for defined specific period of time between timeMin and timeMax
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    nowdate = datetime.datetime.utcnow()
    now = nowdate.isoformat() + 'Z' # 'Z' indicates UTC time
    maxDate = datetime.datetime(nowdate.year,nowdate.month,nowdate.day,23,59,59).isoformat() + 'Z'   # right now time period for detecting the events in calendar is set for one day.
    
    new = now.replace("T","-").replace("-"," ").replace(":"," ").split(" ")
    
    nowhour = int(new[3]) - 4 
    nowmin = int(new[4])
   
    # calling 'event' method from google calendar api service to get the list of event for assigned time period. 
    eventsResult = service.events().list(calendarId='primary', timeMin=now, timeMax=maxDate, singleEvents=True, orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print 'No upcoming events found.'
        
    for event in events: # get events in calendar and calculate the events' durations.
            if (event['summary']=='work'):
                start = event['start'].get('dateTime').replace("T","-").replace("-"," ").replace(":"," ").split(" ")
                
                start_hour = int(start[3])
                start_min = int(start[4])

                end = event['end'].get('dateTime').replace("T","-").replace("-"," ").replace(":"," ").split(" ")
                
                end_hour = int(end[3])
                end_min = int(end[4])
                
                sub_hour = end_hour - start_hour
                sub_min = end_min - start_min

                duration = (sub_hour * 60) + sub_min
                #duration = duration - nowmin
                print start, end, event['summary']
                print duration
                # dt is the exact moment that we have to switch between work and rest moods.
                dt =  datetime.datetime(int(start[0]),int(start[1]),int(start[2]),start_hour,start_min,0)
                
                #scheduler schedules 'work' function to be called at the exact time of 'dt'.
                scheduler.add_job(work, 'date', run_date=dt)
                
                #every 60 minutes, 45 minutes for work and 15 minutes for rest is scheduling. 
                for i in range(45,duration-1,60):
                    start_min+=45
                    if start_min>=60 :
                        start_min-=60
                        start_hour+=1
                    dt = datetime.datetime(int(start[0]),int(start[1]),int(start[2]),start_hour,start_min,0)
                    
                    #scheduler schedules 'rest' function to be called at the end of the work period
                    scheduler.add_job(rest, 'date', run_date=dt)
                    
                    #if remaining time for work event is less than 15 minutes, we won't call work function any more. 
                    if end_hour>start_hour+1 or (end_hour==start_hour and end_min-15>start_min) or (end_hour==start_hour+1 and end_min>start_min-45):
                        start_min+=15
                        if start_min>=60 :
                            start_min-=60
                            start_hour+=1
                        dt = datetime.datetime(int(start[0]),int(start[1]),int(start[2]),start_hour,start_min,0)
                        scheduler.add_job(work, 'date', run_date=dt)
                        
                # rest is called always at the end of the work event. 
                dt = datetime.datetime(int(end[0]),int(end[1]),int(end[2]),end_hour,end_min,0)
                scheduler.add_job(rest, 'date', run_date=dt)
                
                
if __name__ == '__main__':
    '''
    'Scheduler:  APScheduler is a Python library that lets you schedule your
    'Python code to be executed later, either just once or periodically.
    ''' 
    '''
    'BackgroundScheduler runs in a thread inside your existing application.
    'Calling start() will start the scheduler and it will continue running
    'after the call returns.
    '''
    scheduler = BackgroundScheduler()
    scheduler.start()
    main()
    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()    