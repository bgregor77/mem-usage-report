import sys
import os
import subprocess
import urllib.parse
import requests
from pprint import pprint
import json

# First make sure we have an active session
try:
  cf_target_result = subprocess.run(['cf','target'], capture_output=True, check=True, encoding='utf-8')
except subprocess.CalledProcessError:
    print('Not logged in. Use \'cf login\' to log in.')
    sys.exit(1)
except:
    print('An unknown error occurred')
    sys.exit(2)

print('Existing session found:')
print(cf_target_result.stdout)

# This is fragile and will break if they change the output of cf target
api_endpoint_line = cf_target_result.stdout.split('\n')[0].split()
api_base_uri = api_endpoint_line[len(api_endpoint_line)-1]

# Now let's establish an OAuth token
try:
  token_request = subprocess.run(['cf','oauth-token'], capture_output=True, check=True, encoding='utf-8')
except subprocess.CalledProcessError:
    print('Not logged in. Use \'cf login\' to log in.')
    sys.exit(1)
except:
    print('An unknown error occurred')
    sys.exit(2)

# Uncomment if you want to snag the bearer token
#print(token_request.stdout)

# Prep our token, headers, and make the initial request
token = token_request.stdout.strip()
headers = {'Authorization':token}
apps_uri = urllib.parse.urljoin(api_base_uri, 'v2/apps')

apps = []

# loop to handle multiple pages of results
done = False
while (not done):
  r = requests.get(apps_uri, headers=headers)
  apps_result = r.json()

  # loop control
  if (apps_result['next_url'] is None):    
    done = True
  else:
    apps_uri = urllib.parse.urljoin(api_base_uri, apps_result['next_url']) # set next page

  for app in apps_result['resources']:
    apps.append(app)

print(len(apps),"apps found in Orgs")
running_count = 0
stopped_count = 0
unknown_state = 0
app_details = []

for app in apps:
  
  app_detail_uri = urllib.parse.urljoin(api_base_uri,os.path.join('v2/apps/',app['metadata']['guid'],'stats'))
  r = requests.get(app_detail_uri, headers=headers)
  app_detail_result = r.json()

  if ('0' in app_detail_result.keys()):
    for items in app_detail_result:
        if app_detail_result[items]['state'] == "RUNNING":
            app_details.append(
                                {
                                  "instance number" : items,
                                  "app-name": app_detail_result[items]['stats']['name'],
                                  "state"  : app_detail_result[items]['state'],
                                  "mem-usage": app_detail_result[items]['stats']['usage']['mem']/1048576,
                                  "mem-quota" : app_detail_result[items]['stats']['mem_quota']/1048576,
                                  "percentage" : round(((app_detail_result[items]['stats']['usage']['mem'] /
                                                  app_detail_result[items]['stats']['mem_quota'])*100),5)
                     }
            )
            running_count = running_count + 1
        else:
            unknown_state = unknown_state + 1

  else:
   # print(app_detail_result['description'])
   stopped_count = stopped_count + 1

pprint(app_details)
print(running_count, " RUNNING instances of apps found")
print(stopped_count, " STOPPED instances of apps found")
print(unknown_state, " UNKNOWN state apps found")
