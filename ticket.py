import mysql.connector
import json
from datetime import date
from datetime import datetime
import threading
import boto3
import string
import random

ticket_nb_lock = threading.Lock()

def convert_datetime_to_str(obj):
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError("Type not serializable")





# Activate CORS
def generate_common_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS, POST, GET, PUT, DELETE', 
        'Access-Control-Max-Age': '86400'
    }       

####### _______________ get ticket by id  _______________ #######

def get_ticket_by_id(cursor, ticket_id):
    select_query = "SELECT * FROM ticket WHERE id = %s"
    cursor.execute(select_query, (ticket_id,))
    ticket = cursor.fetchone()
    if ticket:
        formatted_ticket = {
            'id': ticket[0],
            'ticket_guarantee_number': ticket[1],
            'ticket_ball_number': ticket[2],
            'double': ticket[3],

            'price': ticket[4],
            'state': ticket[5],
            'purchase_date': convert_datetime_to_str(ticket[6]),
            'user_id': ticket[7],
            'user_phone': ticket[8],
            'draw_id': ticket[9],
        }
        return formatted_ticket
    else:
        return None


####### _______________ get all_tickets  _______________ #######

def get_all_tickets(cursor):
    select_query = "SELECT * FROM ticket"
    cursor.execute(select_query)
    tickets = cursor.fetchall()
    formatted_tickets = []
    for ticket in tickets:
        formatted_ticket = {
            'id': ticket[0],
            'ticket_guarantee_number': ticket[1],
            'ticket_ball_number': ticket[2],
            'double': ticket[3],

            'price': ticket[4],
            'state': ticket[5],
            'purchase_date': convert_datetime_to_str(ticket[6]),

            'user_id': ticket[7],
            'user_phone': ticket[8],
            'draw_id': ticket[9],
        }
        formatted_tickets.append(formatted_ticket)
    return formatted_tickets


####### _______________ get ticketby user_id  _______________ #######

def get_tickets_by_user_id(cursor, user_id):
    select_query = "SELECT * FROM ticket WHERE user_id = %s"
    cursor.execute(select_query, (user_id,))
    tickets = cursor.fetchall()
    formatted_tickets = []
    for ticket in tickets:
        formatted_ticket = {
            'id': ticket[0],
            'ticket_guarantee_number': ticket[1],
            'ticket_ball_number': ticket[2],
            'double': ticket[3],
            'price': ticket[4],
            'state': ticket[5],
            'purchase_date': convert_datetime_to_str(ticket[6]),
            'user_id': ticket[7],
            'user_phone': ticket[8],
            'draw_id': ticket[9],
        }
        formatted_tickets.append(formatted_ticket)
    return formatted_tickets

    
####### _______________ get ticket_type  _______________ #######
    
def get_game_type(cursor, game_id):
    try:
        print("  game id = ", game_id)

        select_game_type_query = "SELECT game_type FROM game WHERE id = %s"
        cursor.execute(select_game_type_query, (game_id,))
        game_type = cursor.fetchone()
        print("  game type = ", game_type)

        if game_type is not None:
            print(f"Game type for game_id {game_id}: {game_type[0]}")
            return game_type[0]
        else:
            print(f"No game type found for game_id {game_id}")
            return None
    except Exception as e:
        print(f"Error while fetching game type for game_id {game_id}: {e}")
        return None



####### _______________ get price  _______________ #######

def get_price(cursor, purchase_date, ticket_type):
    print("i m in get price")
    print("purchase_date:", purchase_date)
    print("ticket_type:", ticket_type)
    select_price_query = "SELECT price FROM ticket_price WHERE end_date > %s AND start_date < %s AND ticket_type = %s"
    cursor.execute(select_price_query, (purchase_date, purchase_date, ticket_type,))
    price = cursor.fetchone()
    print(price)
    if price is not None:
        return price[0]
    else:
        return None


####### _______________ code guarantee  for GU and B _______________ #######

def get_numberseq(cursor, draw_id):
    print("I'm in get_numberseq")
    select_query = "SELECT MAX(CAST(SUBSTRING_INDEX(ticket_guarantee_number, ' ', 1) AS UNSIGNED)) FROM ticket WHERE draw_id = %s"
    cursor.execute(select_query, (draw_id,))
    result = cursor.fetchone()
    
    if result and result[0] is not None:
        seq_number = result[0] + 1
    else:
        seq_number = 1

    print("seq_number: ", seq_number)
    return seq_number



def get_random_letters(length):
    print("I'm in get_random_letters")

    letters = string.ascii_uppercase
    random_letters= ''.join(random.choice(letters) for _ in range(length))
    print("random_letters:"  ,random_letters)

    return random_letters
    
    
def get_code_guarantee(cursor, draw_id):
    sequential_part = get_numberseq(cursor, draw_id)
    random_letters = get_random_letters(2)
    ticket_guarantee_number = f"{sequential_part}{random_letters}"
    return ticket_guarantee_number




    
####### _______________ get phone number  _______________ #######

def get_phone_number(token):
    cognito_client = boto3.client('cognito-idp', region_name='eu-west-3')
    response = cognito_client.get_user(
        AccessToken=token
    )
    userAttributes = response['UserAttributes']
    for atr in userAttributes:
        if atr['Name'] == 'phone_number':
            phone = atr['Value']
    return phone
        
    
####### _______________ insert ticket for GU draw  _______________ #######
def insert_for_guarantee_draw(cursor,conn, event, draw_id, game_id, game_type):
    try:
        print("I'm in insert ticket for GU draw")

        print("the ticket is with type :", game_type)

        user_id = event["requestContext"]["authorizer"]["sub"]
        print("user_id:", user_id)

        user_phone = get_phone_number(event['headers']['Authorization'])
        print("user_phone:", user_phone)

        purchase_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("purchase_date:", purchase_date)

        ticket_guarantee_number = get_code_guarantee(cursor, draw_id)
        print("ticket_guarantee_number:", ticket_guarantee_number)

        # Fetch and consume the results of the previous query
        cursor.fetchall()

        price = get_price(cursor, purchase_date, game_type)
        print("price:", price)

        # Fetch and consume the results of the previous query
        cursor.fetchall()

        state = "active"
        double = 0  # Set to 0 for False, 1 for True

        insert_query = "INSERT INTO ticket (ticket_guarantee_number, `double`, price, state, purchase_date, user_id, user_phone, draw_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        values = (ticket_guarantee_number, double, price, state, purchase_date, user_id, user_phone, draw_id)
        cursor.execute(insert_query, values)
        conn.commit()

        response = {
            "statusCode": 200,
            "body": "Ticket inserted successfully"
        }
        return response
    except Exception as e:
        response = {
            "statusCode": 500,
            "body": json.dumps({'error': str(e)})
        }
        return response


  ####### _______________ insert ticket for B ( daily or weekly ) draw  _______________ #######
def insert_for_boule_draw(cursor,conn, event, draw_id, game_id, game_type,ticket_ball_number):

    try:
        print(" i m in simple ball  draw")
        print("the ticket is with type :", game_type)

        user_id = event["requestContext"]["authorizer"]["sub"]
        user_phone = get_phone_number(event['headers']['Authorization'])

        purchase_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ticket_guarantee_number = get_code_guarantee(cursor, draw_id)

        price = get_price(cursor, purchase_date, game_type)
        state = "active"
        double = 0  # Set to 0 for False, 1 for True

        insert_query = "INSERT INTO ticket (ticket_guarantee_number,ticket_ball_number, `double`, price, state, purchase_date, user_id, user_phone, draw_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (ticket_guarantee_number, ticket_ball_number,double, price, state, purchase_date, user_id, user_phone, draw_id)
        cursor.execute(insert_query, values)
        conn.commit()

        response = {
            "statusCode": 200,
            "body": "Ticket inserted successfully"
        }
        return response
    except Exception as e:
        response = {
            "statusCode": 500,
            "body": json.dumps({'error': str(e)})
        }
        return response
 
 
  ####### _______________ insert double ticket for 2 draw B ( daily or weekly )  _______________ #######
 
 
def insert_double_ticket(cursor,conn, event, draw_id, draw_id_double, ticket_ball_number, ticket_ball_number_double):
    try:
        body = json.loads(event['body'])
        print(" i m in insert ticket for two  ball  draws")

        user_id = event["requestContext"]["authorizer"]["sub"]
        user_phone = get_phone_number(event['headers']['Authorization'])
        purchase_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        state = "active"
        double = 1  # Set to 0 for False, 1 for True
        price = get_price(cursor, purchase_date,'D')

        cursor.fetchall()

        # Insert ticket for draw_id1 
        ticket_guarantee_number1 = get_code_guarantee(cursor, draw_id)

        cursor.execute(
            "INSERT INTO ticket (ticket_guarantee_number, ticket_ball_number, `double`, price, state, purchase_date, user_id, user_phone, draw_id) "
            "VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            ( ticket_guarantee_number1, ticket_ball_number,double, price, state, purchase_date, user_id, user_phone, draw_id)
        )
        conn.commit()


        cursor.fetchall()

        # Insert ticket for draw_id2 and ticket_type2
        ticket_guarantee_number2 = get_code_guarantee(cursor, draw_id_double)
        cursor.fetchall()

        cursor.execute(
            "INSERT INTO ticket (ticket_guarantee_number, ticket_ball_number, `double`, price, state, purchase_date, user_id, user_phone, draw_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (ticket_guarantee_number2, ticket_ball_number_double,double, price,state, purchase_date, user_id, user_phone, draw_id_double)
        )
        conn.commit()
        response = {
            "statusCode": 200,
            "body": "Tickets and ch inserted successfully"
        }
        return response
    except Exception as e:
        response = {
            "statusCode": 500,
            "body": json.dumps({'error': str(e)})
           
        }
        return response

    
            # -------------------------------------------    HTTP methods   ------------------------------------------------------------------  

    
    
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
            
            # -------------------------------------------    GET method   ------------------------------------------------------------------  
            if "httpMethod" in event and event["httpMethod"] == "GET" and "admin" in event["resource"]:
                # Check if both 'id' and 'id_user' parameters are provided in the pathParameters or queryStringParameters
                if event.get('pathParameters') and 'id' in event['pathParameters'] and event.get('queryStringParameters') and 'id_user' in event['queryStringParameters']:
                    response = {
                        "statusCode": 400,
                        "body": "Only one of 'id' or 'id_user' parameters should be provided",
                        "headers": generate_common_headers()
                    }
                else:
                    # Check if the 'id' parameter is provided in the pathParameters
                    if event.get('queryStringParameters') and 'id' in event['queryStringParameters']:
                        ticket_id = event['queryStringParameters']['id']
                        ticket = get_ticket_by_id(cursor, ticket_id)
                        if ticket:
                            response = {
                                "statusCode": 200,
                                "body": json.dumps(ticket, default=convert_datetime_to_str),
                                "headers": generate_common_headers()
                            }
                        else:
                            response = {
                                "statusCode": 404,
                                "body": "Ticket not found",
                                "headers": generate_common_headers()
                            }
                    # Check if the 'id_user' parameter is provided in the queryStringParameters
                    elif event.get('queryStringParameters') and 'id_user' in event['queryStringParameters']:
                        user_id = event['queryStringParameters']['id_user']
                        if user_id is not None:
                            tickets = get_tickets_by_user_id(cursor, user_id)
                            response = {
                                "statusCode": 200,
                                "body": json.dumps(tickets),
                                "headers": generate_common_headers()
                            }
                        else:
                            response = {
                                "statusCode": 400,
                                "body": "User ID not provided in the query string",
                                "headers": generate_common_headers()
                            }
                    else:
                        # If neither 'id' nor 'id_user' parameter is provided, it means the request is for getting all tickets
                        tickets = get_all_tickets(cursor)
                        response = {
                            "statusCode": 200,
                            "body": json.dumps(tickets),
                            "headers": generate_common_headers()
                        }
            # -------------------------------------------  GET method for player  (OKAY)    ------------------------------------------------------------------        

            elif "httpMethod" in event and event["httpMethod"] == "GET" and "player" in event["resource"]:
                    user_id = event["requestContext"]["authorizer"]["sub"]

                    if user_id is not None:
                            tickets = get_tickets_by_user_id(cursor, user_id)
                            response = {
                                "statusCode": 200,
                                "body": json.dumps(tickets),
                                "headers": generate_common_headers()
                            }
                    else:
                            response = {
                                "statusCode": 400,
                                "body": "User ID not provided ",
                                "headers": generate_common_headers()
                            }
                            
                            
             # -------------------------------------------  POST method (OKAY)    ------------------------------------------------------------------        
            elif "httpMethod" in event and event["httpMethod"] == "POST": 
                user_id = event["requestContext"]["authorizer"]["sub"]
                
                # from request
                request_body = json.loads(event["body"])
                draw_id = request_body.get("draw_id")
                game_id = request_body.get("game_id")
                double = request_body.get("double_ticket")  # Assuming the front-end sends the 'double' value
                draw_id_double = request_body.get("draw_id_double")
                ticket_ball_number = request_body.get("ticket_ball_number")
                ticket_ball_number_double = request_body.get("ticket_ball_number_double")
                
                # doivent etre entrer : draw_id ,game_id   ,double 
                # Check if required values are provided
                if draw_id is None or game_id is None or double is None:
                    response = {
                        "statusCode": 400,
                        "body": "Required parameters (draw_id, game_id, double_ticket) are missing in the request body",
                        "headers": generate_common_headers()

                    }
                    cursor.close()
                    conn.commit()
                    return response
    
                # Get the game type based on the game_id
                game_type = get_game_type(cursor,game_id)
                print
                if not game_type:
                    response = {
                        "statusCode": 400,
                        "body": "Invalid game_id, game in not found.",
                        "headers": generate_common_headers()

                    }
                    cursor.close()
                    conn.commit()
                    return response

                # Check the game type and call the appropriate insert function
                if game_type == "GU":
                    #
                    print("I m in GU  game")

                    response=insert_for_guarantee_draw(cursor,conn, event, draw_id, game_id,game_type)
                    return response
                    
                elif game_type in ["BW", "BD"]:
                    if double:
                        # doivent etre entrer : ticket_ball_number,  draw_id_double, ticket_ball_number_double

                        if ticket_ball_number is None or draw_id_double is None or ticket_ball_number_double is None:
                            response = {
                                "statusCode": 400,
                                "body": "Required parameters (ticket_ball_number,  draw_id_double, ticket_ball_number_double) are missing in the request body",
                                "headers": generate_common_headers()

                            }
                            cursor.close()
                            conn.commit()
                            return response
                        else :
                            response = insert_double_ticket(cursor,conn, event, draw_id, draw_id_double, ticket_ball_number, ticket_ball_number_double)

                    else:
                        if ticket_ball_number is None:
                            response = {
                                "statusCode": 400,
                                "body": "Required parameters (ticket_ball_number) are missing in the request body",
                                 "headers": generate_common_headers()

                            }
                            cursor.close()
                            conn.commit()
                            return response
                        else:
                            response = insert_for_boule_draw(cursor,conn, event, draw_id, game_id,game_type, ticket_ball_number)
                else:
                    response = {
                        "statusCode": 400,
                        "body": "Invalid game type.",
                        "headers": generate_common_headers()

                    }
                
               
                return response

            # -------------------------------------------------------------------------------------------------------------------------------------------       
            else:
                response = {
                    "statusCode": 400,
                    "body": "Invalid HTTP method",
                    "headers": generate_common_headers()

                }

            cursor.close()
            conn.commit()
            conn.close()

            return response
       
        return response
    except Exception as e:
        response = {
            "statusCode": 500,
            "body": str(e),
            "headers": generate_common_headers()

        }
        return response
