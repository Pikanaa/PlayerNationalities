import re
from graphqlclient import GraphQLClient
import json
from operator import itemgetter
import sys

##ENTER YOUR API KEY HERE
authToken = 'YOUR_API_KEY'

if(authToken == 'YOUR_API_KEY'):
    authToken = input('Paste your api key or add your smash.gg API key in the .py file if you don\'t want to bother with it everytime.\n')

def addParticipant(list,country):
    done = False
    for sublist in list:
        if sublist[0] == country:
            sublist[1] += 1
            done = True
            break;
    if not done:
        list.append([country,1])
    return list

class HorsIntervalle(Exception):
    pass

phaseId = None
perPage = 100
apiVersion = 'alpha'
unassigned = []
countries = []
total = -1

client = GraphQLClient('https://api.smash.gg/gql/' + apiVersion)
client.inject_token('Bearer ' + authToken)

tournament = input("Tournament? (part between smash.gg/tournament/ and the following /)\n")
query = '''
    query tournaments($slug: String) {
        tournament(slug:$slug) {
            events{
                id
                name
                videogame {
                    id
                    name
                }
                phases{
                    id
                    name
                }
            }
        }
    }
'''
var = dict(
{
    "slug":tournament
})

try:
    result = client.execute(query,var)
except Exception:
    input('Cannot connect to smash.gg, make sure your internet connection is working or that your API key is correct.')
    exit()
resData = json.loads(result)

i = 1
if(resData['data']['tournament'] == None):
    input("Tournament not recognized, try again")
    exit()

print("\nEvents:")
for event in resData['data']['tournament']['events']:
    print(str(i) + "- " + event['name'] + " | " + event['videogame']['name'])
    i+=1

event = 0
while True:
    try:
        event = int(input("\nWhich event are you interested in?\n"))
        if (event < 1) or (event >= i):
            raise HorsIntervalle
        break
    except (HorsIntervalle, ValueError):
        print("Enter the id of the event you're interested in using the list above.")

phases = resData['data']['tournament']['events'][event-1]['phases']

i = 1
print("\nPhases:")
for phase in resData['data']['tournament']['events'][event-1]['phases']:
    print(str(i) + "- " + phase['name'])
    i+=1

phase = 0
while True:
    try:
        phase = int(input("\nWhich phase are you interested in?\n"))
        if (phase < 1) or (phase >= i):
            raise HorsIntervalle
        break
    except (HorsIntervalle, ValueError):
        print("Enter the id of the phase you're interested in using the list above.")

phaseId = resData['data']['tournament']['events'][event-1]['phases'][phase-1]['id']

query = '''
query pages($phaseId: ID, $perPage: Int) {
    phase(id:$phaseId) {
        seeds(query: {
          perPage: $perPage
        }){
            pageInfo {
                total
                totalPages
            }
        }
    }
}
'''
var = dict(
{
    "phaseId": phaseId,
    "perPage": perPage
})

result = client.execute(query,var)
resData = json.loads(result)

total = resData['data']['phase']['seeds']['pageInfo']['total']

print("\nRetrieving data... (this might take a while based on the number of participants)")

for page in range(1,resData['data']['phase']['seeds']['pageInfo']['totalPages']+1):
    query = '''
        query PhaseSeeds($phaseId: ID, $page: Int, $perPage: Int) {
          phase(id:$phaseId) {
            seeds(query: {
              page: $page
              perPage: $perPage
            }){
              pageInfo {
                total
                totalPages
              }
              nodes {
                id
                seedNum
                entrant {
                  participants {
                    gamerTag
                        player {
                          user{
                        location {
                          country
                        }
                      }
                        }
                  }
                }
              }
            }
          }
        }
    '''
    var = dict(
    {
      "phaseId":phaseId,
      "page": page,
      "perPage": perPage
    })

    result = client.execute(query,var)

    resData = json.loads(result)
    if 'errors' in resData:
        print('Error:')
        print(resData['errors'])
    else:
        for player in resData['data']['phase']['seeds']['nodes']:
            user = player['entrant']['participants'][0]['player']['user']
            if user == None or user['location'] == None :
                unassigned.append(player['entrant']['participants'][0]['gamerTag'])
            else:
                country = user['location']['country']
                if country == None:
                    unassigned.append(player['entrant']['participants'][0]['gamerTag'])
                else:
                    countries = addParticipant(countries,country)

countries = sorted(countries,key=itemgetter(1),reverse=True)
print("\nTotal participants: "+str(total))
print("\nCountry\t#P".expandtabs(30))
for country in countries:
    print((country[0]+'\t'+str(country[1])).expandtabs(30))
if len(unassigned)>0:
    print("\n"+str(len(unassigned))+" players with unknown nationalities")
    choice = input("Do you want the full list? (y/n)\n")
    if(choice == "yes") or (choice == "y"):
        for player in unassigned:
            print(player)

input("Press ENTER to leave the program.")
