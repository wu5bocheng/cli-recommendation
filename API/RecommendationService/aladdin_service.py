import os
import requests
import json
import logging
from .util import RecommendationSource


def get_recommend_from_aladdin(command_list, correlation_id, subscription_id, cli_version, user_id, top_num=50):  # pylint: disable=unused-argument
    '''query next command from web api'''

    url = os.environ["Aladdin_Service_URL"]

    headers = {
        'Content-Type': 'application/json'
    }
    if user_id:
        headers["X-UserId"] = user_id

    payload = {
        "history": get_cmd_history(command_list),
        "clientType": "AzureCli",
        "context": {
            "versionNumber": cli_version    
        },
        "numberOfPredictions": top_num
    }
    if correlation_id:
        payload["context"]["CorrelationId"] = correlation_id
    if subscription_id:
        payload["context"]["SubscriptionId"] = subscription_id

    response = requests.post(url, json.dumps(payload), headers=headers)
    if response.status_code != 200:
        logging.info('Status:{} {} ErrorMessage:{}'.format(response.status_code, response.reason, response.text))
        return []
    return transform_response(response)


def get_cmd_history(command_list):
    command_data = json.loads(command_list)
    if len(command_data) == 0:
        return "start_of_snippet\nstart_of_snippet"
    if len(command_data) == 1 or os.environ["Aladdin_History_Command"] == "1":
        return "start_of_snippet\n" + get_cmd_data(command_data[-1])
    return get_cmd_data(command_data[-2]) + '\n' + get_cmd_data(command_data[-1])


def get_cmd_data(command_item):
    command_item = json.loads(command_item)
    command_data = command_item['command']
    if 'arguments' in command_item:
        command_data = '{} {}'.format(command_data, ' *** '.join(command_item['arguments']) + ' ***')
    return command_data


def transform_response(response):
    response_data = json.loads(response.text)
    result = []

    for recommendation_item in response_data:
        items = recommendation_item.split()

        sub_commands = []
        arguments = []
        argument_start = False
        for item in items:
            if item.startswith('-'):
                argument_start = True
                arguments.append(item)
            elif not argument_start and not item.startswith('{'):
                sub_commands.append(item)

        command_info = {
            "command": " ".join(sub_commands),
            "arguments": arguments,
            "source": RecommendationSource.Aladdin
        }
        result.append(command_info)

    return result