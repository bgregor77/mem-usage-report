import sys
import os
import subprocess
import urllib.parse
import requests
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

print(len(apps),"apps found in Org")
count = 0

for app in apps:
  
  app_detail_uri = urllib.parse.urljoin(api_base_uri,os.path.join('v2/apps/',app['metadata']['guid'],'stats'))
  r = requests.get(app_detail_uri, headers=headers)
  app_detail_result = r.json()
  
  if ('0' in app_detail_result.keys()):
    app_name = app_detail_result['0']['stats']['name']
    app_state = app_detail_result['0']['state']
    mem_quota = app_detail_result['0']['stats']['mem_quota']
    mem_usage = app_detail_result['0']['stats']['usage']['mem']
    pct = mem_usage / mem_quota
    print(app_name, '\t' ,app_state, '\tMem Quota:', mem_quota,'\tMem Usage:',mem_usage,'{percent:.2%}'.format(percent=pct))
    count = count + 1
  #else:
  #  print(app_detail_result['description'])

print(count,'RUNNING apps found')