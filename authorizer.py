import json
import jwt
from jwt import PyJWKClient

# Retrieve JWKS (JSON Web Key Set) from the Cognito User Pool
try:
    region = 'eu-west-3'
    userPoolId = 'eu-west-3_lEo2lS9Vr'
    url = (
        f'https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json'
        )
    app_client = '510iir03k9s0og8bdnf7kisf0c'
    jwks_client = PyJWKClient(url)
    
except Exception as e:
    raise Exception("Unable to download JWKS")
    
# Function to generate the authorization response
def return_response(isAuthorized, sub=None, arn=None):
    authResponse = {
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Resource": arn,
                    "Effect": isAuthorized,
                }
            ]
        },
        "context": {
            "sub": sub,
        },
     
    }
    return authResponse
def lambda_handler(event, context):
    print("event")
    print(event)
    arn = event['methodArn']
    try:
        # Extract the authorization token from the event
        token = event['authorizationToken']
        
        # Check if the token has the correct format
        if len(token.split(".")) != 3:
            return return_response(isAuthorized='Deny', arn= arn)
    except Exception as e:
        print(e)
        return return_response(isAuthorized='Deny', arn= arn)
    
    try:
        # Get the unverified header from the token
        headers = jwt.get_unverified_header(token)
        
        # Get the signing key from JWKS and verify the token
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        data = jwt.decode(
            token,
            signing_key.key,
            algorithms=[headers.get("alg")],
            options={
                "verify_signature":True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
                "verify_aud": False,
            },
            )
    except Exception as e:
        # Return Deny response if token verification fails
        return return_response(isAuthorized='Deny', arn= arn)
    try:
        # Check if the client ID matches the expected client ID
        if app_client != data.get("client_id"):
            return return_response(isAuthorized='Deny', arn= arn)
    except Exception as e:
        return return_response(isAuthorized='Deny', arn= arn)
    # Retrieve the user's unique identifier
    sub = data.get("sub")
    
    # Check if the user has the required role
    role = data.get("cognito:groups")
    if '/seller/' in arn and 'SELLERS' not in role:
        return return_response(isAuthorized='Deny', arn= arn)
    elif '/admin/' in arn and 'ADMIN' not in role:
        return return_response(isAuthorized='Deny', arn= arn)
    elif '/player/' in arn and 'PLAYERS' not in role:
        return return_response(isAuthorized='Deny', arn= arn)

    else : 
        return return_response(isAuthorized='Allow',sub=sub, arn= arn) # OKAY