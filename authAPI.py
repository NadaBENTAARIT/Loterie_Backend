import json

import boto3

cognito_client = boto3.client('cognito-idp', region_name='eu-west-3')



# Fonction utilitaire pour générer les en-têtes communs
def generate_common_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS, POST, GET, PUT, DELETE', 
        'Access-Control-Max-Age': '86400'
    }       
    
    
    
    
def lambda_handler(event, context):
    try:
        if event['httpMethod'] == 'OPTIONS':
            # Réponse pour la pré-vérification CORS
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    
                    'Access-Control-Allow-Methods': 'OPTIONS, POST, GET',
                    'Access-Control-Max-Age': '86400'
                }
            }
        elif event['httpMethod'] == 'POST':
            if event['resource'] == '/authentification/signin':
                return handle_signin(event)
            elif event['resource'] == '/player/signup':
                return handle_signupplayer(event)
            elif event['resource'] == '/player/confirmation':
                return handle_confirmation(event)
            elif event['resource'] == '/player/resetpassword':
                return handle_reset_password(event)
            elif event['resource'] == '/player/changepassword':
                return handle_change_password(event)
            elif event['resource'] == '/seller/signup':
                return handle_signupseller(event)
            elif event['resource'] == '/admin/users/sellers/approve':
                return handle_approveseller(event)
            elif event['resource'] == '/admin/users/sellers/reject':
                return handle_rejectseller(event)
            elif event['resource'] == '/refreshtoken'  :
                return handle_refreshAccessToken(event)

        return {
            'statusCode': 404,
            'body': 'Not Found'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }


# -------------------------------------------   SIGN IN method  (for all users)  ------------------------------------------------------------------

def handle_signin(event):
    try:
        body = json.loads(event['body'])
        username = body['username']
        password = body['password']

        response = cognito_client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            },
            ClientId='510iir03k9s0og8bdnf7kisf0c'
        )

        access_token = response['AuthenticationResult']['AccessToken']
        idToken = response['AuthenticationResult']['IdToken']
        refreshToken = response['AuthenticationResult']['RefreshToken']
        return {
            'statusCode': 200,
            'body': json.dumps({
                'accessToken': access_token,
                'idToken' : idToken,
                'refreshToken' : refreshToken,

            }),
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 401,
            'body': str(e),
            'headers': generate_common_headers()
        }
        

        
# -------------------------------------------   SIGN UP Scenario   (for player)  ------------------------------------------------------------------


def handle_signupplayer(event):
    try:
        body = json.loads(event['body'])
        username = body['username']
        password = body['password']
        phone_number = body.get('phone_number')
        email = body.get('email')
        given_name = body.get('given_name')
        family_name = body.get('family_name')

        user_attributes = [
            {
                'Name': 'email',
                'Value': email
            },
            {
                'Name': 'phone_number',
                'Value': phone_number
            }
        ]

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

        response = cognito_client.sign_up(
            ClientId='510iir03k9s0og8bdnf7kisf0c',
            Username=username,
            Password=password,
            UserAttributes=user_attributes
        )

        # Add the user to the "PLAYERS" group
        group_name = 'PLAYERS'
        cognito_client.admin_add_user_to_group(
            UserPoolId='eu-west-3_lEo2lS9Vr',
            Username=username,
            GroupName=group_name
        )

        if phone_number:
            # Send the confirmation code via SMS
            # ...
            message = 'Confirmation code sent via SMS'
        else:
            # Send the confirmation code via email
            # ...
            message = 'Confirmation code sent via email'

        return {
            'statusCode': 200,
            'body': json.dumps({'message': message}),
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': str(e),
            'headers': generate_common_headers()
        }
        
        
        
def handle_confirmation(event):
    try:
        body = json.loads(event['body'])
        username = body['username']
        confirmation_code = body['confirmation_code']

        response = cognito_client.confirm_sign_up(
            ClientId='510iir03k9s0og8bdnf7kisf0c',
            Username=username,
            ConfirmationCode=confirmation_code
        )

        return {
            'statusCode': 200,
            'body': 'User registration confirmed successfully.',
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_reset_password(event):
    try:
        body = json.loads(event['body'])
        email_or_phone = body['email_or_phone']

        response = cognito_client.forgot_password(
            ClientId='510iir03k9s0og8bdnf7kisf0c',
            Username=email_or_phone
        )

        return {
            'statusCode': 200,
            'body': 'Password reset code sent successfully.',
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_change_password(event):
    try:
        body = json.loads(event['body'])
        username = body['username']
        code = body['code']
        new_password = body['new_password']
        confirm_password = body['confirm_password']

        if new_password != confirm_password:
            return {
                'statusCode': 400,
                'body': 'Passwords do not match.',
                'headers': generate_common_headers()
            }

        response = cognito_client.confirm_forgot_password(
            ClientId='510iir03k9s0og8bdnf7kisf0c',
            Username=username,
            ConfirmationCode=code,
            Password=new_password
        )

        return {
            'statusCode': 200,
            'body': 'Password changed successfully.',
            'headers': generate_common_headers()
        }
    except cognito_client.exceptions.CodeMismatchException:
        return {
            'statusCode': 400,
            'body': 'Invalid or expired code.',
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }

# -------------------------------------------   SIGN UP Scenario   (for seller)  ------------------------------------------------------------------
def handle_signupseller(event):
    try:
        body = json.loads(event['body'])
        username = body['username']
        password = body['password']
        phone_number = body.get('phone_number')
        email = body.get('email')
        given_name = body.get('given_name')
        family_name = body.get('family_name')

        user_attributes = [
            {
                'Name': 'email',
                'Value': email
            },
            {
                'Name': 'phone_number',
                'Value': phone_number
            }
        ]

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

        response = cognito_client.sign_up(
            ClientId='510iir03k9s0og8bdnf7kisf0c',
            Username=username,
            Password=password,
            UserAttributes=user_attributes
        )

        # Add the user to the "SELLERS" group
        group_name = 'SELLERS'
        cognito_client.admin_add_user_to_group(
            UserPoolId='eu-west-3_lEo2lS9Vr',
            Username=username,
            GroupName=group_name
        )

        # Send a notification to the administrator for approval
        #admin_email = 'nada123.bentaarit@gmail.com'
        #subject = 'Seller Account Approval Required'
        #message = f"Please approve the seller account registration for username: {username}"
        # Logic to send the email to the administrator
        # ...

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Seller registration submitted for approval'}),
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': str(e),
            'headers': generate_common_headers()
        }
# -------------------------------------------   ADMIN approve seller  ------------------------------------------------------------------
def handle_approveseller(event):
    try:
        body = json.loads(event['body'])
        username = body['username']

        response = cognito_client.admin_confirm_sign_up(
            UserPoolId='eu-west-3_lEo2lS9Vr',
            Username=username
        )

        return {
            'statusCode': 200,
            'body': 'Seller registration confirmed by administrator.',
            'headers': generate_common_headers()

        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': str(e),
            'headers': generate_common_headers()
        }
# -------------------------------------------   ADMIN reject seller  ------------------------------------------------------------------
def handle_rejectseller(event):
    try:
        body = json.loads(event['body'])
        username = body['username']

       # Retirer l'utilisateur du groupe "SELLERS"
        group_name = 'SELLERS'
        cognito_client.admin_remove_user_from_group(
            UserPoolId='eu-west-3_lEo2lS9Vr',
            Username=username,
            GroupName=group_name
        )

        # Supprimer l'utilisateur de Cognito
        cognito_client.admin_delete_user(
            UserPoolId='eu-west-3_lEo2lS9Vr',
            Username=username
        )
        return {
            'statusCode': 200,
            'body': 'Seller registration rejected by administrator and be deleted.',
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': str(e),
            'headers': generate_common_headers()
        }
# -------------------------------------------   Refresh token from cognito  ------------------------------------------------------------------
def handle_refreshAccessToken(event):
    request_body = json.loads(event["body"])
    refreshToken = request_body.get("refreshToken")
    print(refreshToken)
    try:
        response = cognito_client.initiate_auth(
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refreshToken
            },
            ClientId='510iir03k9s0og8bdnf7kisf0c'
        )

        access_token = response['AuthenticationResult']['AccessToken']

        return {
            'statusCode': 200,
            'body': access_token,
            'headers': generate_common_headers()
        }
    except cognito_client.exceptions.NotAuthorizedException:
        return {
            'statusCode': 401,
            'body': 'Invalid refresh token.',
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}',
            'headers': generate_common_headers()
        }
    # return {
    #     'statusCode': 200,
    #     'body': "from refresh token"
    # }    

