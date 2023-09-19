import json
import boto3
import traceback

import mysql.connector
from datetime import date, datetime

# Variables de connexion à la base de données
db_host = 'imperial.cgxxuuxgitss.af-south-1.rds.amazonaws.com'
db_user = 'Imperial_23'
db_password = 'Imperial_admin_2K23'
db_name = 'loto'
db_port = 3306


# Fonction utilitaire pour convertir un objet datetime en chaîne de caractères
def convert_datetime_to_str(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError("Type not serializable")


# Fonction utilitaire pour générer les en-têtes communs
def generate_common_headers():
    return {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS, POST, GET, PUT, DELETE', 
        'Access-Control-Max-Age': '86400'
    }
# Fonction utilitaire pour convertir un objet date en chaîne de caractères
def convert_to_serializable(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# Gestionnaire pour l'API
def lambda_handler(event, context):
    try:
        # Établir la connexion à la base de données
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port
        )

        if conn.is_connected():
            cursor = conn.cursor()

            
            if event['httpMethod'] == 'GET':
               
                if event['resource'] == '/admin/province/{id}':
                    province_id = event['pathParameters']['id']
                    return handle_get_province_by_id(cursor, province_id)
                elif event['resource'] == '/admin/province':
                    return handle_get_all_provinces(cursor)
                elif event['resource'] == '/admin/city/{id}':
                    city_id = event['pathParameters']['id']
                    return handle_get_city_by_id(cursor, city_id)
                elif event['resource'] == '/admin/city':
                    return handle_get_all_cities(cursor)
                elif event['resource'] == '/admin/street/{id}':
                    street_id = event['pathParameters']['id']
                    return handle_get_street_by_id(cursor, street_id)
                elif event['resource'] == '/admin/street':
                    return handle_get_all_streets(cursor)
                elif event['resource'] == '/admin/salespoint/{id}':
                    point_of_sale_id = event['pathParameters']['id']
                    return handle_get_point_of_sale_by_id(cursor, point_of_sale_id)
                elif event['resource'] == '/admin/salespoint':
                    return handle_get_all_points_of_sale(cursor)


            elif event['httpMethod'] == 'POST':
                if event['resource'] == '/admin/province':
                    province_data = json.loads(event['body'])
                    response = handle_create_province(cursor, province_data)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/city':
                    city_data = json.loads(event['body'])
                    response=handle_create_city(cursor, city_data)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/street':
                    street_data = json.loads(event['body'])
                    response = handle_create_street(cursor, street_data)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/salespoint':
                    point_of_sale_data = json.loads(event['body'])
                    response = handle_create_point_of_sale(cursor, point_of_sale_data)
                    conn.commit()
                    return response
                    
            elif event['httpMethod'] == 'PUT':
                if event['resource'] == '/admin/province/{id}':
                    province_id = event['pathParameters']['id']
                    province_data = json.loads(event['body'])
                    response=handle_update_province(cursor, province_id, province_data)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/city/{id}':
                    city_id = event['pathParameters']['id']
                    city_data = json.loads(event['body'])
                    response = handle_update_city(cursor, city_id, city_data)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/street/{id}':
                    street_id = event['pathParameters']['id']
                    street_data = json.loads(event['body'])
                    response = handle_update_street(cursor, street_id, street_data)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/salespoint/{id}':
                    point_of_sale_id = event['pathParameters']['id']
                    point_of_sale_data = json.loads(event['body'])
                    response= handle_update_point_of_sale(cursor, point_of_sale_id, point_of_sale_data)
                    conn.commit()
                    return response

            elif event['httpMethod'] == 'DELETE':
                if event['resource'] == '/admin/province/{id}':
                    province_id = event['pathParameters']['id']
                    response=handle_delete_province(cursor,province_id)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/city/{id}':
                    city_id = event['pathParameters']['id']
                    response=handle_delete_city(cursor, city_id)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/street/{id}':
                    street_id = event['pathParameters']['id']
                    response = handle_delete_street(cursor, street_id)
                    conn.commit()
                    return response
                elif event['resource'] == '/admin/salespoint/{id}':
                    point_of_sale_id = event['pathParameters']['id']
                    response = handle_delete_point_of_sale(cursor, point_of_sale_id)
                    conn.commit()
                    return response
            # Fermer le curseur et la connexion à la base de données
            cursor.close()
            conn.close()
            
          

            return {
                'statusCode': 404,
                'body': 'Not Found'
            }
        else:
            response = {
                'statusCode': 500,
                'body': 'Failed to connect to the database',
            }
            return response
    except Exception as e:
        response = {
            'statusCode': 500,
            'body': str(e), 
        }
        return response


# ------------------------------------ CRUD pour la table "province" ------------------------------------


def handle_get_all_provinces(cursor):
    try:
        select_query = "SELECT * FROM province"
        cursor.execute(select_query)
        provinces = cursor.fetchall()
        formatted_provinces = []
        for province in provinces:
            formatted_province = {
                'id': province[0],
                'name': province[1],
            }
            formatted_provinces.append(formatted_province)
        return {
            'statusCode': 200,
            'body': json.dumps(formatted_provinces),
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }


def handle_get_province_by_id(cursor, province_id):
    try:
        select_query = "SELECT * FROM province WHERE id = %s"
        cursor.execute(select_query, (province_id,))
        province = cursor.fetchone()
        if province:
            formatted_province = {
                'id': province[0],
                'name': province[1],
            }
            return {
                'statusCode': 200,
                'body': json.dumps(formatted_province),
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 404,
                'body': 'Province not found',
                'headers': generate_common_headers()
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_create_province(cursor, province_data):
    try:
        name = province_data.get('name')

        if name:
            insert_query = "INSERT INTO province (name) VALUES (%s)"
            cursor.execute(insert_query, (name,))
            province_id = cursor.lastrowid
            return {
                'statusCode': 200,
                'body': json.dumps({'id': province_id, 'message': 'Province inserted successfully'}),
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 400,
                'body': 'Invalid province data',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_update_province(cursor, province_id, province_data):
    try:
        # Check if the province_id exists before proceeding with the update
        check_query = "SELECT id FROM province WHERE id = %s"
        cursor.execute(check_query, (province_id,))
        existing_province = cursor.fetchone()

        if existing_province:
            name = province_data.get('name')

            if name:
                update_query = "UPDATE province SET name = %s WHERE id = %s"
                cursor.execute(update_query, (name, province_id,))
                return {
                    'statusCode': 200,
                    'body': 'Province updated successfully',
                    'headers': generate_common_headers()
                }
            else:
                return {
                    'statusCode': 400,
                    'body': 'No valid parameters provided for the update',
                    'headers': generate_common_headers()
                }
        else:
            return {
                'statusCode': 404,
                'body': 'Province with the provided ID not found',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }


def handle_delete_province(cursor, province_id):
    try:
        check_query = "SELECT COUNT(*) FROM province WHERE id = %s"
        cursor.execute(check_query, (province_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            delete_query = "DELETE FROM province WHERE id = %s"
            cursor.execute(delete_query, (province_id,))

            return {
                'statusCode': 200,
                'body': 'Province was successfully deleted',
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 400,
                'body': 'Invalid province ID',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'Error occurred while deleting the province',
            'headers': generate_common_headers()
        }


# ------------------------------------ CRUD pour la table "city" ------------------------------------



def handle_get_all_cities(cursor):
    try:
        select_query = "SELECT * FROM city"
        cursor.execute(select_query)
        cities = cursor.fetchall()
        formatted_cities = []
        for city in cities:
            formatted_city = {
                'id': city[0],
                'name': city[1],
                'postal_code': city[2],
                'province_id': city[3],
            }
            formatted_cities.append(formatted_city)
        return {
            'statusCode': 200,
            'body': json.dumps(formatted_cities),
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_get_city_by_id(cursor, city_id):
    try:
        select_query = "SELECT * FROM city WHERE id = %s"
        cursor.execute(select_query, (city_id,))
        city = cursor.fetchone()
        if city:
            formatted_city = {
                'id': city[0],
                'name': city[1],
                'postal_code': city[2],
                'province_id': city[3],
            }
            return {
                'statusCode': 200,
                'body': json.dumps(formatted_city),
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 404,
                'body': 'City not found',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_create_city(cursor, city_data):
    try:
        name = city_data.get('name')
        postal_code = city_data.get('postal_code')
        province_id = city_data.get('province_id')

        if name and postal_code and province_id:
            insert_query = "INSERT INTO city (name, postal_code, province_id) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (name, postal_code, province_id,))
            city_id = cursor.lastrowid
            return {
                'statusCode': 200,
                'body': json.dumps({'id': city_id, 'message': 'City inserted successfully'}),
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 400,
                'body': 'Invalid city data',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_update_city(cursor, city_id, city_data):
    try:
        # Check if the city_id exists before proceeding with the update
        check_query = "SELECT id FROM city WHERE id = %s"
        cursor.execute(check_query, (city_id,))
        existing_city = cursor.fetchone()

        if existing_city:
            name = city_data.get('name')
            postal_code = city_data.get('postal_code')
            province_id = city_data.get('province_id')

            if name and postal_code and province_id:
                update_query = "UPDATE city SET name = %s, postal_code = %s, province_id = %s WHERE id = %s"
                cursor.execute(update_query, (name, postal_code, province_id, city_id,))
                return {
                    'statusCode': 200,
                    'body': 'City updated successfully',
                    'headers': generate_common_headers()
                }
            else:
                return {
                    'statusCode': 400,
                    'body': 'No valid parameters provided for the update',
                    'headers': generate_common_headers()
                }
        else:
            return {
                'statusCode': 404,
                'body': 'City with the provided ID not found',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_delete_city(cursor, city_id):
    try:
        check_query = "SELECT COUNT(*) FROM city WHERE id = %s"
        cursor.execute(check_query, (city_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            delete_query = "DELETE FROM city WHERE id = %s"
            cursor.execute(delete_query, (city_id,))

            return {
                'statusCode': 200,
                'body': 'City was successfully deleted',
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 400,
                'body': 'Invalid city ID',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'Error occurred while deleting the city',
            'headers': generate_common_headers()
        }


# ------------------------------------ CRUD pour la table "street" ------------------------------------
def handle_get_street_by_id(cursor, street_id):
    try:
        select_query = "SELECT * FROM street WHERE id = %s"
        cursor.execute(select_query, (street_id,))
        street = cursor.fetchone()
        if street:
            formatted_street = {
                'id': street[0],
                'name': street[1],
                'city_id': street[2],
            }
            return {
                'statusCode': 200,
                'body': json.dumps(formatted_street),
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 404,
                'body': 'Street not found',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_create_street(cursor, street_data):
    try:
        name = street_data.get('name')
        city_id = street_data.get('city_id')

        if name and city_id:
            insert_query = "INSERT INTO street (name, city_id) VALUES (%s, %s)"
            cursor.execute(insert_query, (name, city_id,))
            street_id = cursor.lastrowid
            return {
                'statusCode': 200,
                'body': json.dumps({'id': street_id, 'message': 'Street inserted successfully'}),
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 400,
                'body': 'Invalid street data',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_update_street(cursor, street_id, street_data):
    try:
        # Check if the street_id exists before proceeding with the update
        check_query = "SELECT id FROM street WHERE id = %s"
        cursor.execute(check_query, (street_id,))
        existing_street = cursor.fetchone()

        if existing_street:
            name = street_data.get('name')
            city_id = street_data.get('city_id')

            if name and city_id:
                update_query = "UPDATE street SET name = %s, city_id = %s WHERE id = %s"
                cursor.execute(update_query, (name, city_id, street_id,))
                return {
                    'statusCode': 200,
                    'body': 'Street updated successfully',
                    'headers': generate_common_headers()
                }
            else:
                return {
                    'statusCode': 400,
                    'body': 'No valid parameters provided for the update',
                    'headers': generate_common_headers()
                }
        else:
            return {
                'statusCode': 404,
                'body': 'Street with the provided ID not found',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }


def handle_delete_street(cursor, street_id):
    try:
        check_query = "SELECT COUNT(*) FROM street WHERE id = %s"
        cursor.execute(check_query, (street_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            delete_query = "DELETE FROM street WHERE id = %s"
            cursor.execute(delete_query, (street_id,))

            return {
                'statusCode': 200,
                'body': 'Street was successfully deleted',
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 400,
                'body': 'Invalid street ID',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'Error occurred while deleting the street',
            'headers': generate_common_headers()
        }
def handle_get_all_streets(cursor):
    try:
        select_query = "SELECT * FROM street"
        cursor.execute(select_query)
        streets = cursor.fetchall()
        formatted_streets = []
        for street in streets:
            formatted_street = {
                'id': street[0],
                'name': street[1],
                'city_id': street[2]
            }
            formatted_streets.append(formatted_street)
        return {
            'statusCode': 200,
            'body': json.dumps(formatted_streets),
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }
    

# ------------------------------------ CRUD pour la table "point_of_sale" ------------------------------------


def handle_get_all_points_of_sale(cursor):
    try:
        select_query = "SELECT * FROM point_of_sale"
        cursor.execute(select_query)
        points_of_sale = cursor.fetchall()

        formatted_points_of_sale = []
        for point_of_sale in points_of_sale:
            formatted_point_of_sale = {
                'id': point_of_sale[0],
                'id_seller': point_of_sale[1],
                'name': point_of_sale[2],
                'device_code': point_of_sale[3],
                'fiscal_code': point_of_sale[4],
                'street_id': point_of_sale[5]
                
            }
            formatted_points_of_sale.append(formatted_point_of_sale)

        return {
            'statusCode': 200,
            'body': json.dumps(formatted_points_of_sale),
            'headers': generate_common_headers()
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }



def handle_get_point_of_sale_by_id(cursor, point_of_sale_id):
    try:
        select_query = "SELECT * FROM point_of_sale WHERE id = %s"
        cursor.execute(select_query, (point_of_sale_id,))
        point_of_sale = cursor.fetchone()
        if point_of_sale:
            formatted_point_of_sale = {
                'id': point_of_sale[0],
                'id_seller': point_of_sale[1],
                'name': point_of_sale[2],
                'device_code': point_of_sale[3],
                'fiscal_code': point_of_sale[4],
                'street_id': point_of_sale[5],
                
            }
            return {
                'statusCode': 200,
                'body': json.dumps(formatted_point_of_sale),
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 404,
                'body': 'Point of sale not found',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }

def handle_create_point_of_sale(cursor, point_of_sale_data):
    try:
        id_seller = point_of_sale_data.get('id_seller')
        name = point_of_sale_data.get('name')
        device_code = point_of_sale_data.get('device_code')
        fiscal_code = point_of_sale_data.get('fiscal_code')
        street_id = point_of_sale_data.get('street_id')

        if id_seller and name and device_code and fiscal_code and street_id:
            # Check if the id_seller exists in the "SELLERS" group of the Cognito user pool
            user_pool_id = 'eu-west-3_lEo2lS9Vr'  # Replace with your actual Cognito user pool ID
            seller_username = id_seller  # Replace with the username of the seller
            if not is_user_in_group(user_pool_id, seller_username, 'SELLERS'):
                return {
                    'statusCode': 403,
                    'body': 'The provided id_seller does not exist in the SELLERS group.',
                    'headers': generate_common_headers()
                }

            # If the id_seller exists, proceed with the insert operation
            insert_query = "INSERT INTO point_of_sale (id_seller, name, device_code, fiscal_code, street_id) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (id_seller, name, device_code, fiscal_code, street_id,))
            point_of_sale_id = cursor.lastrowid
            return {
                'statusCode': 200,
                'body': json.dumps({'id': point_of_sale_id}),
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 400,
                'body': 'Invalid point of sale data',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e),
            'headers': generate_common_headers()
        }
def is_user_in_group(user_pool_id, username, group_name):
    client = boto3.client('cognito-idp', region_name='eu-west-3')
    try:
        response = client.admin_list_groups_for_user(UserPoolId=user_pool_id, Username=username)
        groups = response['Groups']
        print("///////////  ", groups)
        return any(group['GroupName'] == group_name for group in groups)
    except client.exceptions.UserNotFoundException:
        # Handle the case where the user (seller) is not found in the Cognito user pool
        return False
    except Exception as e:
        # Handle any other unexpected errors
        print(f"An error occurred while checking user group: {e}")
        return False

def handle_update_point_of_sale(cursor, point_of_sale_id, point_of_sale_data):
    try:
        id_seller = str(point_of_sale_data.get('id_seller'))  # Convert to string
        name = point_of_sale_data.get('name')
        device_code = point_of_sale_data.get('device_code')
        fiscal_code = point_of_sale_data.get('fiscal_code')
        street_id = point_of_sale_data.get('street_id')

        if id_seller and name and device_code and fiscal_code and street_id:
            # Check if the id_seller exists in the "SELLERS" group of the Cognito user pool
            user_pool_id = 'eu-west-3_lEo2lS9Vr'  # Replace with your actual Cognito user pool ID
            seller_username = id_seller  # Replace with the username of the seller
            if not is_user_in_group(user_pool_id, seller_username, 'SELLERS'):
                return {
                    'statusCode': 403,
                    'body': 'The provided id_seller does not exist.',
                    'headers': generate_common_headers()
                }
            print("***********************************")

            # Check if the point of sale ID exists in the database
            check_query = "SELECT id FROM point_of_sale WHERE id = %s"
            cursor.execute(check_query, (point_of_sale_id,))
            existing_point_of_sale = cursor.fetchone()

            if not existing_point_of_sale:
                return {
                    'statusCode': 404,
                    'body': 'Point of sale not found with the provided ID.',
                    'headers': generate_common_headers()
                }

            update_query = "UPDATE point_of_sale SET id_seller = %s, name = %s, device_code = %s, fiscal_code = %s, street_id = %s WHERE id = %s"
            cursor.execute(update_query, (id_seller, name, device_code, fiscal_code, street_id, point_of_sale_id,))
            rows_affected = cursor.rowcount
            if rows_affected > 0:
                return {
                    'statusCode': 200,
                    'body': 'Point of sale updated successfully',
                    'headers': generate_common_headers()
                }
            else:
                return {
                    'statusCode': 500,
                    'body': 'Any change point of sale.',
                    'headers': generate_common_headers()
                }
        else:
            return {
                'statusCode': 400,
                'body': 'No valid parameters provided for the update',
                'headers': generate_common_headers()
            }
    except Exception as e:
        traceback.print_exc()  # Add this line to print the full traceback
        return {
            'statusCode': 500,
            'body': 'An error occurred while processing the request.',
            'headers': generate_common_headers()
        }
        
        
        
def handle_delete_point_of_sale(cursor, point_of_sale_id):
    try:
        check_query = "SELECT COUNT(*) FROM point_of_sale WHERE id = %s"
        cursor.execute(check_query, (point_of_sale_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            delete_query = "DELETE FROM point_of_sale WHERE id = %s"
            cursor.execute(delete_query, (point_of_sale_id,))
            
            return {
                'statusCode': 200,
                'body': 'Point of sale was successfully deleted',
                'headers': generate_common_headers()
            }
        else:
            return {
                'statusCode': 400,
                'body': 'Invalid point of sale ID',
                'headers': generate_common_headers()
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'Error occurred while deleting the point of sale',
            'headers': generate_common_headers()
        }
