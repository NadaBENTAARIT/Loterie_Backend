import json
import mysql.connector
from datetime import date, datetime

def generate_common_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS, POST, GET, PUT, DELETE', 
        'Access-Control-Max-Age': '86400'
    }       
    

def lambda_handler(event, context):
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
            # Vérifier et traiter les différentes méthodes HTTP et ressources
            if event['httpMethod'] == 'GET':
                if event['resource'] == '/draw': 
                    query_params = event['queryStringParameters']
                    limit = int(query_params['limit'])
                    offset = int(query_params['offset'])
                    return handle_get_all_draws(cursor, limit, offset)
                elif event['resource'] == '/draw/{id}':         
                    draw_id = event['pathParameters']['id']
                    return handle_get_draw_by_id(cursor, draw_id)
                elif event['resource'] == '/admin/draw/{id}/result/potential':
                    draw_id = event['pathParameters']['id']
                    response = handle_result_drawn_ball_numbers(cursor, draw_id)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/draw/{id}/result/guarantee':
                    draw_id = event['pathParameters']['id']
                    response = handle_get_result_guarantee_number(cursor, draw_id)
                    return response
                    
            elif event['httpMethod'] == 'PUT':
                if event['resource'] == '/admin/draw/{id}':
                    draw_id = event['pathParameters']['id']
                    draw_data = json.loads(event['body'])
                    response = handle_update_draw_date(cursor, draw_id, draw_data)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/draw/{id}/result/potential':   
                    draw_id = event['pathParameters']['id']
                    draw_data = json.loads(event['body'])
                    response = handle_put_drawn_ball_numbers(cursor, draw_id, draw_data)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/draw/{id}/result/guarantee': 
                    draw_id = int(event['pathParameters']['id'])
                    response = handle_result_guarantee_number(cursor, draw_id)
                    conn.commit()
                    return response
            cursor.close()
            conn.close()
            return {
                'statusCode': 404,
                'body': 'Not Found',
                'headers': generate_common_headers()
            }
        else:
            response = {
                'statusCode': 500,
                'body': 'Failed to connect to the database',
                'headers': generate_common_headers()
            }
            return response
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }
        return response


# -------------------------------------------    GET LIST method   ------------------------------------------------------------
def handle_get_all_draws(cursor, limit, offset):
    select_query = """
        SELECT d.id, d.draw_date, d.drawn_guarantee_number, d.drawn_ball_numbers, g.id as game_id,  g.name, g.game_type
        FROM game g, draw d
        where g.id = d.game_id
        ORDER BY d.id asc
        LIMIT %s OFFSET %s
    """
    cursor.execute(select_query, (limit,offset))
    draws = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    formatted_draws = [
        dict(zip(column_names, draw))
        for draw in draws
    ]
    status_dict = {True: "actif", False: "inactif"}
    system_date = datetime.now()
    for draw in formatted_draws:
        draw["status"] = status_dict[draw["draw_date"] > system_date]
  
    return {
        'statusCode': 200,
        'body': json.dumps(formatted_draws, default=convert_datetime_to_str),
        'headers': generate_common_headers()
    }
# -------------------------------------------    GET BY ID   ------------------------------------------------------------------
def handle_get_draw_by_id(cursor, draw_id):
    select_query = """
        select d.id, d.draw_date, d.drawn_guarantee_number, d.drawn_ball_numbers, g.id as game_id,  g.name as game_name, g.game_type
        from game g, draw d
         where g.id = d.game_id
        and  d.id = %s
    """
    cursor.execute(select_query, (draw_id,))
    draw = cursor.fetchone()
    if draw:
        column_names = [desc[0] for desc in cursor.description]
        formatted_draw = dict(zip(column_names, draw))
        system_date = datetime.now()
        if formatted_draw["draw_date"] > system_date:
            formatted_draw["status"] = "actif"
        else:
            formatted_draw["status"] = "inactif"
  
        return {
            "statusCode": 200,
            "body": json.dumps(formatted_draw, default=convert_datetime_to_str),
            'headers': generate_common_headers()
        }
    else:
        return {
            'statusCode': 404,
            'body': 'Tirage non trouvé.',
            'headers': generate_common_headers()
        }


# # -------------------------------------------    PUT draw date  -------------------------------------------------------------
def handle_update_draw_date(cursor, draw_id, draw_data):
    select_query = "SELECT game_id FROM draw WHERE id = %s"
    cursor.execute(select_query, (draw_id,))
    game_id = cursor.fetchone()
    if game_id is not None:
        draw_date = datetime.strptime(draw_data.get('draw_date'), '%Y-%m-%dT%H:%M:%SZ')
        select_query = "SELECT end_date FROM game WHERE id = %s"
        cursor.execute(select_query, game_id)
        end_date = cursor.fetchone()[0]
        if draw_date > end_date:
            update_query = "UPDATE draw SET draw_date = %s WHERE id = %s"
            cursor.execute(update_query, (draw_date, draw_id))
            return {
                'statusCode': 200,
                'body': 'Date du tirage définie avec succès.',
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 400,
                'body': 'La date du tirage doit être postérieure à la date de fin du jeu. (draw_date > ' + str(end_date) + ')',
                'headers': generate_common_headers()
            }
    else:
        return {
            'statusCode': 404,
            'body': 'Tirage non trouvé.',
            'headers': generate_common_headers()
        }

# -------------------------------------------    put  drawn_ball_numbers  -----------------------------------------------------
def handle_put_drawn_ball_numbers(cursor, draw_id, draw_data):
    drawn_ball_numbers = draw_data.get('drawn_ball_numbers')
    select_query = "SELECT game_type, drawn_ball_numbers, draw_date FROM draw d, game g  WHERE d.game_id = g.id and d.id = %s"
    cursor.execute(select_query, (draw_id,))
    result = cursor.fetchone()
    if result is not None:
        game_type = result[0]
        if game_type == "GU":
            return {
                'statusCode': 400,
                'body': 'Type jeu Gros Lot ne supporte pas des gagnants potentils.',
                'headers': generate_common_headers()
            }
        ball_numbers = result[1]    
        if ball_numbers is not None :
            return {
                'statusCode': 400,
                'body': "Les numéros de boules sont déjà insérés",
                'headers': generate_common_headers()
            }
            
        draw_date = result[2]
        system_date = datetime.now()
        if system_date <=  draw_date : 
            return {
                'statusCode': 400,
                'body': "le tirage peut être fait à la date de tirage",
                'headers': generate_common_headers()
            } 
        update_draw_query = "UPDATE draw SET drawn_ball_numbers = %s, updated_at = %s WHERE id = %s"
        cursor.execute(update_draw_query, (drawn_ball_numbers, system_date, draw_id))
        return {
            'statusCode': 200,
            'body': 'Les numéros de balles tirées ont été mis à jour avec succès.',
            'headers': generate_common_headers()
        }
    else:
        return {
            'statusCode': 400,
            'body': 'Le tirage n\'existe pas.',
            'headers': generate_common_headers()
        }
   
#----------------------------------   result for guarantee code     -----------------------------------------------------------
def handle_result_guarantee_number(cursor, draw_id ):
    select_query = "SELECT draw_date, drawn_guarantee_number FROM draw  WHERE id = %s"
    cursor.execute(select_query, (draw_id,))
    result = cursor.fetchone()
    if result is None :
        return {
            'statusCode': 400,
            'body': 'Le tirage n\'existe pas.',
            'headers': generate_common_headers()
        }
    else :
        draw_date = result[0]
        drawn_guarantee_number = result[1]
        
        system_date = datetime.now()
        if system_date <=  draw_date : 
            return {
                'statusCode': 400,
                'body': "le tirage peut être fait à la date de tirage",
                'headers': generate_common_headers()
            } 
        
        if drawn_guarantee_number is not None : 
            return { 
                'statusCode': 400,
                'body': 'Le tirage est déja fait.',
                'headers': generate_common_headers()
            }
        else :
            verif_query = "SELECT count(*) from ticket where draw_id = %s"
            cursor.execute(verif_query, (draw_id,))
            nb = cursor.fetchone()[0]
            if nb == 0:
                return {
                    'statusCode': 400,
                    'body': "Pas de ticket",
                    'headers': generate_common_headers()
                }
            select_random_index_query = "SELECT  FLOOR(RAND() * COUNT(*)) AS random_index FROM ticket WHERE draw_id = %s"
            cursor.execute(select_random_index_query, (draw_id,))
            random_index = int(cursor.fetchone()[0])
            
            select = "SELECT ticket_guarantee_number FROM ticket WHERE draw_id = %s LIMIT 1 OFFSET %s "
            cursor.execute(select, (draw_id, random_index))
            ticket_guarantee_number =  cursor.fetchone()[0]
            
            updated_at = datetime.now()
            
            update_ticket_query = "UPDATE ticket SET state = %s WHERE draw_id = %s AND ticket_guarantee_number = %s"
            cursor.execute(update_ticket_query, ("gagnant", draw_id, ticket_guarantee_number))
    
            update_ticket_query = "UPDATE ticket SET state = %s WHERE draw_id = %s AND ticket_guarantee_number != %s and state != %s "
            cursor.execute(update_ticket_query, ("désactivé", draw_id, ticket_guarantee_number, "gagnant"))
            
            insert_guarantee_number = "UPDATE draw SET drawn_guarantee_number = %s, updated_at = %s WHERE id = %s "
            cursor.execute(insert_guarantee_number, (ticket_guarantee_number,system_date, draw_id) ) 
            
            return {
                'statusCode': 200,
                'body': json.dumps({'guarantee_number': ticket_guarantee_number}),
                'headers': generate_common_headers()
            }
            
        
        
#----------------------------------  Get  winning ticket (guarantee code)     -----------------------------------------------------------
def handle_get_result_guarantee_number(cursor, draw_id):
    select_guarantee_number = "SELECT drawn_guarantee_number FROM draw WHERE id = %s"
    cursor.execute(select_guarantee_number, (draw_id,))
    guarantee_number = cursor.fetchone()
    if guarantee_number:
        guarantee_number = guarantee_number[0]
        select_ticket = "SELECT * FROM ticket WHERE draw_id = %s AND ticket_guarantee_number = %s"
        cursor.execute(select_ticket, (draw_id, guarantee_number))
        
        ticket = cursor.fetchone()
        if ticket:
            column_names = [desc[0] for desc in cursor.description]
            formatted_ticket = dict(zip(column_names, ticket))
            return {
                "statusCode": 200,
                "body": json.dumps(formatted_ticket, default=convert_datetime_to_str),
                'headers': generate_common_headers()
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Ticket introuvable."}),
                'headers': generate_common_headers()
            }
    else :
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Tirage non existant."}),
            'headers': generate_common_headers()
        }
        

       
#----------------------------------   4,5,6    --------------------------------------------------------------------------------

def handle_result_drawn_ball_numbers(cursor, draw_id):
    select_ball_numbers = "SELECT drawn_ball_numbers FROM draw WHERE id = %s"
    cursor.execute(select_ball_numbers, (draw_id,))
    ball_numbers = cursor.fetchone()
    if ball_numbers : 
        ball_numbers = ball_numbers[0]
        if ball_numbers is None :
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Pas de numéros de Boule."}),
                'headers': generate_common_headers()
            }
        else : 
            ball_numbers = ball_numbers.split('-') 
            ball_numbers = [item.strip() for item in ball_numbers]  
            select_all_tickets = "SELECT * FROM ticket WHERE draw_id = %s"
            cursor.execute(select_all_tickets, (draw_id,))
            tickets = cursor.fetchall()
            if tickets : 
                column_names = [column[0] for column in cursor.description]
                formatted_tickets = [
                    dict(zip(column_names, ticket))
                    for ticket in tickets
                ]
                all_tickets = {
                    "4": [],
                    "5": [],
                    "6": []
                }
                for ticket in formatted_tickets:
                    nb = 0
                    ticket_ball_number = ticket["ticket_ball_number"]
                    for num in ball_numbers:
                        if str(num) in ticket_ball_number:
                            nb += 1
                            ticket_ball_number = ticket_ball_number.replace(str(num), "--", 1)
                    if str(nb) in all_tickets:
                        all_tickets[str(nb)].append(ticket)
                
                
                # --------
                update_winner_query = "UPDATE ticket SET state = %s WHERE draw_id = %s AND id = %s"
                update_non_winner_query = "UPDATE ticket SET state = %s WHERE draw_id = %s AND state != %s"
                for ticket_category in ['4', '5', '6']:
                    for ticket in all_tickets[ticket_category]:    
                        cursor.execute(update_winner_query, ("gagnant", draw_id, ticket["id"]))
                        cursor.execute(update_non_winner_query, ("désactivé", draw_id, "gagnant"))
                return {
                    'statusCode': 200,
                    'body':  json.dumps(all_tickets, default=convert_datetime_to_str),
                    'headers': generate_common_headers()
                }
            else :
                return {
                    "statusCode": 404,
                    "body": json.dumps({"message": "Pas de ticket vendu"}),
                    'headers': generate_common_headers()
                }
                
    else : 
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Tirage non existant."}),
            'headers': generate_common_headers()
        }
    
# -------------------------------   Convert datetime -> STR -------------------------------------------------------------------
def convert_datetime_to_str(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError("Type not serializable")


