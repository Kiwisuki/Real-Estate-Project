import json

def lambda_handler(event, context):
    transactionId = event['queryStringParamaters']['transactionId']
    transactionType = event['queryStringParamaters']['type']
    transactionAmount = event['queryStringParamaters']['amount']

    transactionResponse = {}
    transactionResponse['Id'] = transactionId
    transactionResponse['type'] = transactionType
    transactionResponse['amount'] = transactionAmount
    transactionResponse['message'] = 'Hello from lambda'



    responseObject = {}
    responseObject['statusCode'] = 200
    responseObject['headers'] = {}
    responseObject['headers']['Content-Type'] = 'application/json'
    responseObject['body'] = json.dumps(transactionResponse)
    return responseObject


