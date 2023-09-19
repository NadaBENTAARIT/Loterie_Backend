import json
import boto3







# Activate CORS
def generate_common_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS, POST, GET, PUT, DELETE', 
        'Access-Control-Max-Age': '86400'
    }       


cognito_client = boto3.client('cognito-idp', region_name='eu-west-3')

def lambda_handler(event, context):
    if event["httpMethod"] == "GET" and event['resource'] == '/profile':
        try:
            token = event['headers']['Authorization']
            response = cognito_client.get_user(
                AccessToken=token
            )
            attributes = response['UserAttributes']
            formatted_user = {}
            for i in range(len(attributes)):
                attribute_name = attributes[i]['Name']
                attribute_value = attributes[i]['Value']
                formatted_user[attribute_name] = attribute_value
                
            return {
                'statusCode': 200,
                'body': json.dumps( formatted_user  ),
                "headers": generate_common_headers()

            }
        except Exception as e:
            return {
                'statusCode': 401,
                'body': str(e),
                "headers": generate_common_headers()

            }
    elif event["httpMethod"] == "POST":
        token = event['headers']['Authorization']

        if event['resource'] == '/profile/changepassword':
            try:
                request_body = json.loads(event["body"])
                previousPassword = request_body.get("previousPassword")
                proposedPassword = request_body.get("proposedPassword")
                response = cognito_client.change_password(
                    PreviousPassword=previousPassword,
                    ProposedPassword=proposedPassword,
                    AccessToken=token
                )
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    return {
                        'statusCode': 200,
                        'body': "Mot de passe modifié avec succès.",
                        "headers": generate_common_headers()

                    }
            except Exception as e:
                return {
                    'statusCode': 401,
                    'body': str(e),
                    "headers": generate_common_headers()

                }
        elif event['resource'] == '/profile/globalsignout':
            try:
                response = cognito_client.global_sign_out(
                    AccessToken=token
                )
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    return {
                        'statusCode': 200,
                        'body': "Processus de déconnexion globale terminé avec succès.",
                        "headers": generate_common_headers()

                    }
            except Exception as e:
                return {
                    'statusCode': 401,
                    'body': str(e),
                    "headers": generate_common_headers()
                    }

        elif event['resource'] == '/profile/signoutdevice':
            try:
                response_get_user = cognito_client.get_user(
                    AccessToken=token
                )
                username = response_get_user['Username']
                response_sign_out = cognito_client.admin_user_sign_out(
                    UserPoolId='eu-west-3_lEo2lS9Vr',
                    Username=username
                )
                if response_sign_out['ResponseMetadata']['HTTPStatusCode'] == 200:
                    return {
                        'statusCode': 200,
                        'body': "User signed out from the current device successfully.",
                        "headers": generate_common_headers()

                    }
            except Exception as e:
                return {
                    'statusCode': 401,
                    'body': str(e),
                    "headers": generate_common_headers()
                    }


    elif event["httpMethod"] == "PUT":
        token = event['headers']['Authorization']
        try:
            request_body = json.loads(event["body"])
            given_name = request_body.get("given_name")
            family_name = request_body.get("family_name")
            user_attributes = []
            if given_name:
                user_attributes.append({
                    'Name': 'given_name',
                    'Value': given_name
                })
            if family_name:
                user_attributes.append({
                    'Name': 'family_name',
                    'Value': family_name
                })
            if user_attributes:
                response = cognito_client.update_user_attributes(
                    UserAttributes=user_attributes,
                    AccessToken=token,
                )
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    return {
                        'statusCode': 200,
                        'body': "Les attributs de l'utilisateur ont été mis à jour avec succès.",
                        "headers": generate_common_headers()

                    }
            else:
                return {
                    'statusCode': 400,
                    'body': "Aucun attribut n'a été fourni.",
                    "headers": generate_common_headers()

                }
        except Exception as e:
            return {
                'statusCode': 401,
                'body': str(e),
                "headers": generate_common_headers()

            }
        