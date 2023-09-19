import mysql.connector
import json
from datetime import date, datetime


# Activate CORS
def generate_common_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS, POST, GET, PUT, DELETE', 
        'Access-Control-Max-Age': '86400'
    }       



def convert_datetime_to_str(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError("Type not serializable")

def convert_to_serializable(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def get_ticket_price(cursor, ticket_price_id):
    select_query = "SELECT * FROM ticket_price WHERE id = %s"
    cursor.execute(select_query, (ticket_price_id,))
    ticket_price = cursor.fetchone()
    if ticket_price:
        formatted_ticket_price = {
            'id': ticket_price[0],
            'price': ticket_price[1],
            'ticket_type': ticket_price[2],

            'start_date': ticket_price[3],
            'end_date': ticket_price[4]
        }
        return formatted_ticket_price
    else:
        return None

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
            
            # -------------------------------------------    GET method ------------------------------------------------------------------  
            if "httpMethod" in event and event["httpMethod"] == "GET":
                # -------------------------------------------    GET by id  ------------------------------------------------------------------  
                if event.get('pathParameters'):
                    ticket_price_id = event['pathParameters']['id']
                    ticket_price = get_ticket_price(cursor, ticket_price_id)
                    if ticket_price:
                        response = {
                            "statusCode": 200,
                            "body": json.dumps(ticket_price, default=convert_datetime_to_str),
                            "headers": generate_common_headers()
                        }
                    else:
                        response = {
                            "statusCode": 404,
                            "body": "Ticket price not found",
                            "headers": generate_common_headers()

                        }
                # -------------------------------------------    GET all    ------------------------------------------------------------------  
                else:
                    select_query = "SELECT * FROM ticket_price"
                    cursor.execute(select_query)
                    ticket_prices = cursor.fetchall()
                    formatted_ticket_prices = []
                    for ticket_price in ticket_prices:
                        formatted_ticket_price = {
                            'id': ticket_price[0],
                            'price': ticket_price[1],
                            'ticket_type': ticket_price[2],
                            'start_date': convert_datetime_to_str(ticket_price[3]),
                            'end_date': convert_datetime_to_str(ticket_price[4])
                        }
                        formatted_ticket_prices.append(formatted_ticket_price)
                    response = {
                        "statusCode": 200,
                        "body": json.dumps(formatted_ticket_prices),
                        "headers": generate_common_headers()

                    }
                    
                    
            # -------------------------------------------    DELETE method (OKAY) ------------------------------------------------------------        
            elif "httpMethod" in event and event["httpMethod"] == "DELETE" :
                if event.get('pathParameters'):
                    ticket_price_id = event['pathParameters']['id']
                    ticket_price = get_ticket_price(cursor, ticket_price_id)
                    if ticket_price:
                        delete_query = "DELETE FROM ticket_price WHERE id = %s"
                        try:
                            cursor.execute(delete_query, (ticket_price_id,))
                            response = {
                                "statusCode": 200,
                                "body": "Le prix du billet a été supprimé avec succès.",
                                "headers": generate_common_headers()

                            }
                        except Exception as e:
                            print(e)
                            response = {
                                "statusCode": 500,
                                "body": "Une erreur s'est produite lors de la suppression du prix du ticket.",
                                "headers": generate_common_headers()

                            }
                    else:
                        response = {
                            "statusCode": 404,
                            "body": "Prix du ticket introuvable.",
                            "headers": generate_common_headers()

                        }
                else:
                    response = {
                        "statusCode": 400,
                        "body": "Requête non valide : paramètres de chemin manquants.",
                        "headers": generate_common_headers()

                    }
            
            
            # -------------------------------------------    UPDATE method (OKAY)  ------------------------------------------------------------------        

            elif "httpMethod" in event and event["httpMethod"] == "PUT" and event['resource'].startswith('/admin/ticket_price/'):
                if event.get('pathParameters'):
                    ticket_price_id = event['pathParameters']['id']
                    request_body = json.loads(event["body"])
                    new_price = request_body.get("price")
                    new_ticket_type = request_body.get("ticket_type")
                    new_start_date = request_body.get("start_date")
                    new_end_date = request_body.get("end_date")
                    
                    # Check if all required fields are present in the request body
                    if new_price is None or new_ticket_type is None or new_start_date is None or new_end_date is None:
                        response = {
                            "statusCode": 400,
                            "body": "Veuillez fournir toutes les valeurs requises dans le corps de la requête.",
                            "headers": generate_common_headers()
                        }
                    # Check if ticket_type is one of the allowed values
                    elif new_ticket_type not in ('GU', 'BW', 'BD', 'D'):
                        response = {
                            "statusCode": 400,
                            "body": "La valeur du champ 'ticket_type' est invalide. Les valeurs autorisées sont 'GU', 'BW', 'BD' et 'D'.",
                            "headers": generate_common_headers()
                        }
                    else:
                        new_start_date = datetime.strptime(new_start_date, '%Y-%m-%dT%H:%M:%SZ')
                        new_end_date = datetime.strptime(new_end_date, '%Y-%m-%dT%H:%M:%SZ')
                        
                        select_query = "SELECT * FROM ticket_price WHERE id = %s"
                        cursor.execute(select_query, (ticket_price_id,))
                        ticket_price = cursor.fetchone()
                        if ticket_price:
                            update_query = "UPDATE ticket_price SET price = %s, ticket_type = %s, start_date = %s, end_date = %s WHERE id = %s"
                            try:
                                cursor.execute(update_query, (new_price, new_ticket_type, new_start_date, new_end_date, ticket_price_id))
                                response = {
                                    "statusCode": 200,
                                    "body": "Prix du ticket mis à jour avec succès.",
                                    "headers": generate_common_headers()
                                }
                            except Exception as e:
                                print(e)
                                response = {
                                    "statusCode": 500,
                                    "body": "Une erreur s'est produite lors de la mise à jour du prix du ticket.",
                                    "headers": generate_common_headers()
                                }
                        else:
                            response = {
                                "statusCode": 404,
                                "body": "Prix du ticket introuvable pour la mise à jour.",
                                "headers": generate_common_headers()
                            }
            
                else:
                    response = {
                        "statusCode": 400,
                        "body": "Requête non valide : paramètres de chemin manquants.",
                        "headers": generate_common_headers()
                    }



            # -------------------------------------------    POST method (OKAY)  ------------------------------------------------------------------        
            elif "httpMethod" in event and event["httpMethod"] == "POST" and event['resource'] == '/admin/ticket_price':
                request_body = json.loads(event["body"])
                price = request_body.get("price")
                ticket_type = request_body.get("ticket_type")
            
                start_date = request_body.get("start_date")
                end_date = request_body.get("end_date")
            
                # Check if all required fields are present in the request body
                if price is None or ticket_type is None or start_date is None or end_date is None:
                    response = {
                        "statusCode": 400,
                        "body": "Veuillez fournir toutes les valeurs requises dans le corps de la requête.",
                        "headers": generate_common_headers()

                    }
                # Check if ticket_type is one of the allowed values
                elif ticket_type not in ('GU', 'BW', 'BD', 'D'):
                    response = {
                        "statusCode": 400,
                        "body": "La valeur du champ 'ticket_type' est invalide. Les valeurs autorisées sont 'GU', 'BW', 'BD' et 'D'.",
                        "headers": generate_common_headers()

                    }
                else:
                    start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ')
                    end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ')
                    
                    insert_query = "INSERT INTO ticket_price (price, ticket_type, start_date, end_date) VALUES (%s, %s, %s, %s)"
                    try:
                        values = (price, ticket_type, start_date, end_date)
                        cursor.execute(insert_query, values)
                        conn.commit()
                        response = {
                            "statusCode": 200,
                            "body": "Prix du ticket inséré avec succès.",
                            "headers": generate_common_headers()

                        }
                    except Exception as e:
                        response = {
                            "statusCode": 500,
                            "body": "Une erreur s'est produite lors de l'insertion du prix du ticket.",
                            "headers": generate_common_headers()

                        }


            
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
        else:
            response = {
                "statusCode": 500,
                "body": "Failed to connect to the database",
                "headers": generate_common_headers()

            }
            return response
    except Exception as e:
        response = {
            "statusCode": 500,
            "body": str(e),
            "headers": generate_common_headers()

        }
        return response
