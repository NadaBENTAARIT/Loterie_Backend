import json
import boto3
from datetime import datetime

cognito_client = boto3.client('cognito-idp', region_name='eu-west-3')
user_pool_id = 'eu-west-3_lEo2lS9Vr'

# Fonction utilitaire pour générer les en-têtes communs
def generate_common_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS, POST, GET, PUT, DELETE', 
        'Access-Control-Max-Age': '86400'
    }       
    
def convert_to_serializable(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    
def lambda_handler(event, context):
    if event["httpMethod"] == 'GET' and event['resource'] == '/admin/users/{id}':
        ids = event['pathParameters']['id']
        try:
            response = cognito_client.admin_get_user(
                UserPoolId=user_pool_id,
                Username=ids
            )
            
            user_attributes = response['UserAttributes']
            formatted_user = {}
            for attribute in user_attributes:
                attribute_name = attribute['Name']
                attribute_value = attribute['Value']
                formatted_user[attribute_name] = attribute_value
            formatted_user["UserStatus"] = response["UserStatus"]
            formatted_user["Enabled"] = response["Enabled"]

            return {
                'statusCode': 200,
                'body': json.dumps(formatted_user),
                'headers': generate_common_headers()
            }
        except cognito_client.exceptions.UserNotFoundException:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'User not found.'}),
                'headers': generate_common_headers()
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Error retrieving the user.', 'error': str(e)}),
                'headers': generate_common_headers()
            }
        
       
    
    elif event["httpMethod"] == 'GET' and event['resource'] != '/admin/users/{id}':
        query_params = event['queryStringParameters']
        # ----------------------------------- Get users in group ------------------------------
        if query_params is not None:
            group = query_params['group']
            print(group)
            if group not in ["ADMIN", "PLAYERS", "SELLERS"]:
                return {
                    'statusCode': 400,
                    'body': "Group doesn't exist",
                    'headers': generate_common_headers()

                }
            response = cognito_client.list_users_in_group(
                UserPoolId=user_pool_id,
                GroupName=group
            )
            users = response['Users']
            formatted_users = []
            for user in users:
                attributes = user['Attributes']
                formatted_user = {}
                for i in range(len(attributes)):
                    attribute_name = attributes[i]['Name']
                    attribute_value = attributes[i]['Value']
                    formatted_user[attribute_name] = attribute_value
                formatted_user["UserStatus"] = user["UserStatus"]
                formatted_user["Enabled"] = user["Enabled"]
                formatted_users.append(formatted_user)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'Users' : formatted_users
                }),
                'headers': generate_common_headers()

            }
        # ----------------------------------- Get all users ------------------------------
        else:
            response = cognito_client.list_users(
                UserPoolId=user_pool_id,
                AttributesToGet=[
                    'email_verified',
                    'phone_number',
                    'given_name',
                    'family_name',
                    'email'
                ],
            )
            users = response['Users']
            print(users)
            formatted_users = []
            for user in users:
                attributes = user['Attributes']
                formatted_user = {}
                for i in range(len(attributes)):
                    attribute_name = attributes[i]['Name']
                    attribute_value = attributes[i]['Value']
                    formatted_user[attribute_name] = attribute_value
                formatted_user["UserStatus"] = user["UserStatus"]
                formatted_user["Enabled"] = user["Enabled"]
                formatted_users.append(formatted_user)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'Users' : formatted_users
                }),
                'headers': generate_common_headers()

            }
    # -------------------------------------------------------------------------------------------------------------
    elif "httpMethod" in event and event["httpMethod"] == "POST":
        
        # -------------------------------------------  Disable User   ------------------------------------------------------------------
        if event['resource'] == '/admin/users/disable':
            if event["body"]:
                try:
                    request_body = json.loads(event["body"])
                    username = request_body.get("username")
                    response = cognito_client.admin_disable_user(
                        UserPoolId=user_pool_id,
                        Username=username
                    )
                    return {
                        'statusCode': 200,
                        'body': "L'utilisateur a été désactivé avec succès.",
                        'headers': generate_common_headers()

                    }
                except Exception as e:
                    return {
                        'statusCode': 500,
                        'body': str(e),
                        'headers': generate_common_headers()

                    }
                   
            else:
                return {
                    'statusCode': 400,
                        'body': "Le nom d'utilisateur n'a pas été fourni.",
                        'headers': generate_common_headers()

                }
                
        # # -------------------------------------------  Enable User   ------------------------------------------------------------------
        elif event['resource'] == '/admin/users/enable':
            if event["body"]:
                try:
                    request_body = json.loads(event["body"])
                    username = request_body.get("username")
                    response = cognito_client.admin_enable_user(
                        UserPoolId=user_pool_id,
                        Username=username
                    )
                    return {
                        'statusCode': 200,
                        'body': "L'utilisateur a été activer avec succès.",
                        'headers': generate_common_headers()

                    }
                except Exception as e:
                    return {
                        'statusCode': 500,
                        'body': str(e),
                        'headers': generate_common_headers()

                    }
                   
            else:
                return {
                    'statusCode': 400,
                        'body': "Le nom d'utilisateur n'a pas été fourni.",
                        'headers': generate_common_headers()

                }
            