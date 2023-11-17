#################################################################################
import boto3
import json
import requests
from requests_aws4auth import AWS4Auth
# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')

#Openseach configuration
def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
host = 'https://search-photos-qr6fhrkwevbrxfp6ecuxvl2o5y.aos.us-east-1.on.aws' # The OpenSearch domain endpoint with https://
index = 'photos'
url = host + '/' + index + '/_search'
headers = { "Content-Type": "application/json" }
auth = get_awsauth('us-east-1', 'es')


def lambda_handler(event, context):
    print("event: ")
    print(event)
    #last_user_message = event['params']['querystring']['q']
    last_user_message = event['params']['querystring']['q']
    
    # change this to the message that user submits on 
    # your website using the 'event' variable
    print(f"Message from frontend: {last_user_message}")
    response = client.recognize_text(
            botId='9B1LPNAAJZ', # MODIFY HERE
            botAliasId='TSTALIASID', # MODIFY HERE
            localeId='en_US',
            sessionId='testuser',
            text=last_user_message)
    keywords = []
    print(response)
    # Check if the slot 'keyword1' exists
    keyword1 = response['sessionState']['intent']['slots']['Keyword1']['value']['interpretedValue']

    keywords.append(keyword1)
    keyword2 = response['sessionState']['intent']['slots']['Keyword2']

    if keyword2 is not None:
        keyword2 = keyword2['value']['interpretedValue']
        keywords.append(keyword2)
    
            
    print(keywords)
    
    # find result from opensearch
    bucket_url = "https://photoalb1.s3.amazonaws.com/"
    
    query = {
      "query": {
        "terms_set": {
          "labels": {
            "terms": keywords,
            "minimum_should_match_script": {
              "source": "1"
            },
          }
        }
      }
    }
    # query = {
    #         "size": 1,
    #         "query": {
    #             "function_score" : {
    #             "query" : { "query_string": { "query": 'test5.jpg' } }
    #             }
    #         }
    # }

    esResp = requests.get(url, auth=auth, headers=headers, data=json.dumps(query))
    data = json.loads(esResp.text)
    print("opensearch return:")
    print(data)
    
    photos = []
    
    esData = data["hits"]["hits"]
    for photo in esData:
        photo_detail = {
            'url': bucket_url+photo['_source']['objectKey'],
            'labels': photo['_source']['labels']
        }
        photos.append(photo_detail)
    print(photos)
    
    if len(photos) > 0:
        print(f"Message from Chatbot: {keywords}")
        print(response)
        resp = {
            'statusCode': 200,
            'body': {
                "results": photos
            }
        }
        print('resp:', resp)
        return resp
    else:
        resp = {
            'statusCode': 400,
            'body': "Nothing from LF2!"
        }
        return resp
