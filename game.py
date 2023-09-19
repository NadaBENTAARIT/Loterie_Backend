import mysql.connector
import json
from datetime import datetime
import boto3

# Fonction utilitaire pour générer les en-têtes communs
def generate_common_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS, POST, GET, PUT, DELETE', 
        'Access-Control-Max-Age': '86400'
    }   

def lambda_handler(event, context):
    # Variables de connexion à la base de données
    db_host = 'imperial.cgxxuuxgitss.af-south-1.rds.amazonaws.com'
    db_user = 'Imperial_23'
    db_password = 'Imperial_admin_2K23'
    db_name = 'loto'
    db_port = 3306
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port
        )
        if conn.is_connected():
            cursor = conn.cursor()
            if "httpMethod" in event and event["httpMethod"] == 'POST' and event['resource'] == '/admin/game':
                user_id = event["requestContext"]["authorizer"]["sub"]
                game_data = json.loads(event["body"])
                response = handle_create_game(cursor, game_data, user_id)
                conn.commit()
                return response
            elif "httpMethod" in event and event["httpMethod"] == "GET" :
                if event.get('pathParameters'):
                    game_id = event['pathParameters']['id']
                    return handle_get_game_by_id(cursor, game_id)
                else:
                    query_params = event['queryStringParameters']
                    limit = int(query_params['limit'])
                    offset = int(query_params['offset'])
                    return handle_get_all_games(cursor, limit, offset)
            elif "httpMethod" in event and event["httpMethod"] == "PUT" :
                if  event['resource'] == '/admin/game/{id}': 
                    game_id = event['pathParameters']['id'] 
                    request_body = json.loads(event["body"])
                    response = handle_update_game (cursor, request_body, game_id)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/game/{id}/enable':
                    game_id = event['pathParameters']['id']
                    return handle_enable_game(cursor, game_id)
                elif event['resource'] == '/admin/game/{id}/disable':
                    game_id = event['pathParameters']['id']
                    return handle_disable_game(cursor, game_id)
            elif "httpMethod" in event and event["httpMethod"] == 'DELETE':
                game_id = event['pathParameters']['id']
                response = handle_delete_game(cursor, game_id)
                conn.commit()
                return response
            else:
                return {
                    "statusCode": 404,
                    "body": "Method Not Found"
                }
    except mysql.connector.Error as err:
        return {
            "statusCode": 500,
            "body": "Database error: " + str(err)
        }
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()



# ----------------------------------------------    enable periodic GAME     -----------------------------------------
def handle_enable_game(cursor, game_id):
    check_query = "SELECT id FROM game WHERE id = %s"
    cursor.execute(check_query, (game_id,))
    row = cursor.fetchone()
    if row is None:
        return {
            'statusCode': 404,
            'body': 'Jeu introuvable dans la base de données.',
            'headers': generate_common_headers()
        }
    client = boto3.client('events')
    rule_name = f'drawRule-{game_id}'
    try:
        response_enable = client.enable_rule(Name=rule_name, EventBusName='default')
        return {
            "statusCode": 200,
            "body": "La règle de planification a été activée.",
            'headers': generate_common_headers()
        }
    except client.exceptions.ResourceNotFoundException:
        return {
            'statusCode': 404,
            'body': 'Règle introuvable dans EventBridge.',
            'headers': generate_common_headers()
        }
# ----------------------------------------------    disable periodic GAME     -----------------------------------------       
def handle_disable_game(cursor, game_id): 
    check_query = "SELECT id FROM game WHERE id = %s"
    cursor.execute(check_query, (game_id,))
    row = cursor.fetchone()
    
    if row is None:
        return {
            'statusCode': 404,
            'body': 'Jeu introuvable dans la base de données.',
            'headers': generate_common_headers()
        }
    client = boto3.client('events')
    rule_name = f'drawRule-{game_id}'

    try:
        response_disable = client.disable_rule(Name=rule_name, EventBusName='default')
        return {
            "statusCode": 200,
            "body": "La règle de planification a été désactivée.",
            'headers': generate_common_headers()
        }
    except client.exceptions.ResourceNotFoundException:
        return {
            'statusCode': 404,
            'body': 'Règle introuvable dans EventBridge.',
            'headers': generate_common_headers()
        }
# ----------------------------------------------    create GAME     -----------------------------------------
def create_cron_expression(end_date, game_type):
    hour = end_date.time()
    if game_type == "BD":
        return f'cron({hour.minute} {hour.hour} * * ? *)'
    elif game_type == "BW":
        day = end_date.weekday() 
        day_mapping = {
            0: 2,
            1: 3,
            2: 4,
            3: 5,
            4: 6,
            5: 7,
            6: 1,
        }
        day = day_mapping[day]
        return f'cron({hour.minute} {hour.hour} ? * {day} *)'
def handle_create_game(cursor, game_data, user_id):
    try :
        name = game_data.get("name")
        start_date = datetime.strptime(game_data.get("start_date"), '%Y-%m-%dT%H:%M:%SZ')
        end_date = datetime.strptime(game_data.get("end_date"), '%Y-%m-%dT%H:%M:%SZ')
        scheduled_draw_date = datetime.strptime(game_data.get("scheduled_draw_date"), '%Y-%m-%dT%H:%M:%SZ')
        prize_amount = game_data.get("prize_amount")
        game_type = game_data.get("type")
    
        created_at  = datetime.now()
        
        # Check if start_date < end_date
        if start_date >= end_date:
            return {
                "statusCode": 404,
                "body": "La date de fin de jeu doit être postérieure à la date de début de jeu.",
                'headers': generate_common_headers()
            }
        elif scheduled_draw_date < end_date:
            return {
                "statusCode": 404,
                "body": "La date du tirage planifié doit être postérieure à la date de fin de jeu",
                'headers': generate_common_headers()
            }
        elif start_date < created_at :
            return {
                "statusCode": 404,
                "body": "La date de début du jeu doit être à jour.",
                'headers': generate_common_headers()
            }
        else:
            # Insert the game
            insert_game_query = "INSERT INTO game (name, game_type, start_date, end_date, prize_amount, user_id, scheduled_draw_date ) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            values = (name, game_type, start_date, end_date, prize_amount, user_id, scheduled_draw_date)
            cursor.execute(insert_game_query, values)
            game_id = cursor.lastrowid
            
            insert_draw_query = "INSERT INTO draw (game_id, created_at, draw_date) VALUES (%s, %s, %s)"
            cursor.execute(insert_draw_query, (game_id, created_at, scheduled_draw_date))
            # ---------------- Guarantee and unique
            if game_type == "GU":                              
                return {
                    "statusCode": 200,
                    "body": "Jeu Gros Lot créé avec succès. Son tirage est planifié.",
                    'headers': generate_common_headers()
                }
                
            # --------------------------------- repetitive game
            elif game_type  in ["BW", "BD"] :
                client_events = boto3.client('events')
                client_lambda = boto3.client('lambda')
                lambda_function_arn = 'arn:aws:lambda:af-south-1:078884298290:function:drawCROn'
                rule_name = f'drawRule-{game_id}'
                print("end date = ")
                print(end_date)
                cron_expression = create_cron_expression(end_date, game_type)
                
                # Define the rule
                response = client_events.put_rule(
                    Name=rule_name,
                    ScheduleExpression=cron_expression,
                    State='ENABLED',
                    Description='Rule to invoke the Cron Lambda function frequently.',
                    EventBusName='default'
                )
                # Select target
                response = client_events.put_targets(
                    Rule=rule_name,
                    Targets=[
                        {
                            'Arn': lambda_function_arn,
                            'Id': 'DrawCronTarget',
                            'Input': f'{{"game_id": "{game_id}"}}'
                        }
                    ]
                )
                
                response = client_lambda.add_permission(
                    FunctionName=lambda_function_arn.split(':')[-1],
                    StatementId=f'{rule_name}-eventbridge',
                    Action='lambda:InvokeFunction',
                    Principal='events.amazonaws.com',
                    SourceArn=f'arn:aws:events:af-south-1:078884298290:rule/{rule_name}'
                )
               
                return {
                    "statusCode": 200,
                    "body": "Jeu répétitif créé avec succès. La création des tirages est planifiée.",
                    'headers': generate_common_headers()
                }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'Une erreur s\'est produite lors de la création du jeu : '+str(e)
        }
        
        
# ----------------------------------------------   get by GAME by id -----------------------------------------   
def handle_get_game_by_id (cursor, game_id):
    select_query = "SELECT  * FROM game g where id = %s"
    cursor.execute(select_query, (game_id,))
    game = cursor.fetchone()
    if game is not None:
        column_names = [desc[0] for desc in cursor.description]
        formatted_game = dict(zip(column_names, game))
        system_date = datetime.now()
        if formatted_game["end_date"] < system_date:
            formatted_game["status"] = "terminé"
        elif formatted_game["start_date"] < system_date:
            formatted_game["status"] = "commencé"
        else : 
            formatted_game["status"] = "à venir"
        return {
            "statusCode": 200,
            "body": json.dumps(formatted_game, default=convert_datetime_to_str),
            'headers': generate_common_headers()
        }
    else:
        return {
            "statusCode": 404,
            "body": "Jeu introuvable.",
            'headers': generate_common_headers()
        }
# ----------------------------------------------   get all GAMEs -----------------------------------------  
def handle_get_all_games (cursor, limit, offset):
    client = boto3.client('events')
    select_query = " SELECT * FROM game ORDER BY id asc LIMIT %s OFFSET %s "
    cursor.execute(select_query, (limit,offset))
    games = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    formatted_games = [
        dict(zip(column_names, game))
        for game in games
    ]
    
   
    system_date = datetime.now()
    for game in formatted_games:
        game_type = game["game_type"]
        if game_type == "BW":
            game_id = game["id"]
            response = client.describe_rule(
                Name=f'drawRule-{game_id}',
                EventBusName='default'
            ) 
            print(response)
            game["enable"] = response['State'] == "ENABLED"
        elif game_type == "BD" :
            game_id = game["id"]
            response = client.describe_rule(
                Name=f'drawRule-{game_id}',
                EventBusName='default'
            ) 
            print(response)
            game["enable"] = response['State'] == "ENABLED"
        
        if game["end_date"] < system_date:
            game["status"] = "terminé"
        elif game["start_date"] < system_date:
            game["status"] = "commencé"
        else : 
            game["status"] = "à venir"
    return {
        "statusCode": 200,
        "body": json.dumps(formatted_games, default=convert_datetime_to_str),
        'headers': generate_common_headers()
    }
# ----------------------------------------------   update GAME -----------------------------------------    
def update_game(cursor, name, prize_amount, new_start_date, new_end_date, new_scheduled_draw_date, game_id):
    update_query = "UPDATE game SET name = %s, start_date = %s, end_date = %s, scheduled_draw_date = %s, prize_amount = %s WHERE id = %s"
    cursor.execute(update_query, (name, new_start_date, new_end_date, new_scheduled_draw_date, prize_amount, game_id))
def update_draw_rule(client, game_id, new_end_date, game_type):
    cron_expression = create_cron_expression(new_end_date, game_type)
    response = client.put_rule(
        Name=f'drawRule-{game_id}',
        ScheduleExpression=cron_expression,
        State='ENABLED'
    )
def handle_update_game (cursor, request_body, game_id):  
    try:
        check_query = "SELECT start_date, game_type FROM game WHERE id = %s"
        cursor.execute(check_query, (game_id,))
        game_info  = cursor.fetchone()
        if game_info :
            start_date, game_type = game_info
            system_date = datetime.now()
            name = request_body.get("name")
            prize_amount = request_body.get("prize_amount")
            new_start_date = datetime.strptime(request_body.get("start_date"), '%Y-%m-%dT%H:%M:%SZ')
            new_end_date = datetime.strptime(request_body.get("end_date"), '%Y-%m-%dT%H:%M:%SZ')
            new_scheduled_draw_date = datetime.strptime(request_body.get("scheduled_draw_date"), '%Y-%m-%dT%H:%M:%SZ')
            if game_type == "GU":
                if start_date < system_date:
                    return {
                        'statusCode': 400,
                        'body': 'Impossible de modifier le jeu car il a déjà commencé.',
                        'headers': generate_common_headers()
                    }
                if new_end_date < new_start_date :
                    return {
                        "statusCode": 404,
                        "body": "La date de fin de jeu doit être postérieure à la date de début de jeu.",
                        'headers': generate_common_headers()
                    }
                if new_scheduled_draw_date < new_end_date:
                    return {
                        "statusCode": 404,
                        "body": "La date du tirage planifié doit être postérieure à la date de fin de jeu.",
                        'headers': generate_common_headers()
                    }
                update_game(cursor, name, prize_amount, new_start_date, new_end_date, new_scheduled_draw_date, game_id)
                return {
                    "statusCode": 200,
                    "body": "Mise à jour du jeu réussie.",
                    'headers': generate_common_headers()
                }
            else :
                update_draw_rule(boto3.client('events'), game_id, new_end_date, game_type)
                update_game(cursor, name, prize_amount, new_start_date, new_end_date, new_scheduled_draw_date, game_id)
                return {
                    'statusCode': 200,
                    'body': 'Mise à jour du jeu réussie.',
                    'headers': generate_common_headers()
                }
        else:
            return {
                'statusCode': 400,
                'body': 'Jeu introuvable.',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'Une erreur s\'est produite lors de la mise à jour du jeu : '+str(e),
            'headers': generate_common_headers()
            
        }
# ----------------------------------------------  delete GAME -----------------------------------------    
def handle_delete_game (cursor, game_id):   
    try:
        check_query = "SELECT start_date FROM game WHERE id = %s"
        cursor.execute(check_query, (game_id,))
        game_info = cursor.fetchone()
        if game_info:
            start_date = game_info[0]
            system_date = datetime.now()
            if start_date > system_date :
                client = boto3.client('events')
                rule_name = f'drawRule-{game_id}'
                response = client.list_rules(
                    NamePrefix=f'drawRule-{game_id}', 
                    EventBusName='default'
                )
                if 'Rules' in response and len(response['Rules']) > 0:
                    response = client.list_targets_by_rule(
                        Rule=rule_name,
                        EventBusName='default'
                    )
                    target_ids = [target['Id'] for target in response['Targets']]
                    response = client.remove_targets(
                        Rule=rule_name,
                        EventBusName='default',
                        Ids=target_ids
                    )
                    response_disable = client.delete_rule(
                        Name=rule_name, 
                        EventBusName='default',
                        Force=True
                    )
                delete_query = "DELETE FROM game WHERE id = %s"
                cursor.execute(delete_query, (game_id,))
                
                return {
                    'statusCode': 200,
                    'body': 'Jeu supprimé avec succès.',
                    'headers': generate_common_headers()
                }
            else:
                return {
                    'statusCode': 400,
                    'body': 'Impossible de supprimer le jeu car il a déjà commencé.',
                    'headers': generate_common_headers()
                }
        else:
            return {
                'statusCode': 400,
                'body': 'Jeu introuvable.',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'Une erreur s\'est produite lors de la suppression du jeu : '+str(e),
            'headers': generate_common_headers()
        }
        
# Fonction utilitaire pour convertir un objet datetime en chaîne de caractères
def convert_datetime_to_str(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError("Type not serializable")
