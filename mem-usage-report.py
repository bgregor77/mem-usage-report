import requests
import click
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = 'https://{}.system.{}.cengage.io'
login_url = base_url.format("login","{}") + '/oauth/token'
api_url = base_url.format("api","{}") + '{}'

def get_auth(foundation,skip,user,password):
    querystring = {
                        "username": user,
                        "password": password,
                        "response_type":"token",
                        "grant_type":"password",
                        "client_id": "cf"
                }

    headers = {
        'authorization': "Basic Y2Y6",
        'accept': "application/json;charset=utf-8"
        }

    response = requests.post(   login_url.format(foundation),
                                headers=headers,
                                params=querystring,
                                verify=skip
                             )
    tokens = response.json()
    tokens['scope'] = tokens['scope'].split()
    return (tokens)

def create_auth_header(access_token):
    return(
        {
            'content-type': "application/json",
            'Authorization': 'bearer ' + access_token
        }
    )

def get_mem_report(header,foundation,skip,endpoint='/v2/apps'):
    apps_uri = api_url.format(foundation,{})
    apps = []

    #loop to handle multiple pages of results
    page_counter = 1
    run = True
    with requests.Session() as s:
        while run:
            params = {
                    "page": page_counter,
                }
            r = s.get(apps_uri.format(endpoint), headers=header,params=params,verify=skip)
            apps_result = r.json()
          # loop control
            if (page_counter == apps_result['total_pages']):
                run = False
            else:
                page_counter = page_counter + 1

            for app in apps_result['resources']:
                apps.append(app)

        print(len(apps),"apps found in Orgs")
        running_count = 0
        stopped_count = 0
        crashed_count = 0
        unknown_count = 0
        app_details = []

        for app in apps:
            app_detail_uri = apps_uri.format(app['metadata']['url']+"/stats")
            r = s.get( app_detail_uri, headers=header, verify=skip)
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
                    elif app_detail_result[items]['state'] == "CRASHED":
                        crashed_count = crashed_count + 1
                        # print("crashed: ", app_detail_uri)
                    else:
                        unknown_count = unknown_count + 1
            else:
                # print("stopped: ", app_detail_uri)
                stopped_count = stopped_count + 1
    s.close()
    # pprint(app_details)
    print(running_count, " RUNNING instances of apps found")
    print(stopped_count, " STOPPED instances of apps found")
    print(crashed_count, " CRASHED instances of apps found")
    print(unknown_count, " UNKNOWN state apps found")


@click.command()
@click.option(
                  '--foundation',
                  default='bumblebee',
                  help = 'target foundation'
              )
@click.option(
                  '--skip-ssl-verification',
                  is_flag=True,
                  help = 'skip ssl verification'
              )
@click.option(
                  "--user",
                  default="",
                  help="username"
              )
@click.option(
                  "--password",
                  default="!",
                  help="password"
              )
def go(foundation,skip_ssl_verification,user,password):
    tokens = get_auth(foundation,  skip_ssl_verification, user,password)
    auth_header = create_auth_header(tokens['access_token'])
    get_mem_report(auth_header,foundation, skip_ssl_verification)

if __name__ == '__main__':
    go()