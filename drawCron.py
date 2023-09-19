import mysql.connector
import json
from datetime import datetime, timedelta

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
            createAt = datetime.now()
            game_id = int(event['game_id'])
            # draw_date = event['draw_date']
            cursor = conn.cursor()

            # check_query = "select count(id) from draw where game_id = %s"
            # cursor.execute(check_query, (game_id,))
            # nb_draw = cursor.fetchone()[0]
            
            # if nb_draw > 0:
            # Recupérer les dates du jeu
            
            select_game_query = "SELECT game_type, start_date, end_date, scheduled_draw_date FROM game where id = %s "
            cursor.execute(select_game_query, (game_id,))
            game = cursor.fetchone()
            game_type = game[0]
            start_date = game[1]
            end_date = game[2]
            scheduled_draw_date = game[3]
        
            if game_type == "BD":
                #incrémenter les dates de 24 heure
                start_date = start_date + timedelta(days=1)
                end_date = end_date + timedelta(days=1)
                scheduled_draw_date = scheduled_draw_date + timedelta(days=1)
               
            elif game_type == "BW":
                #incrémenter les dates d'une semaine
                start_date = start_date + timedelta(weeks=1)
                end_date = end_date + timedelta(weeks=1)
                scheduled_draw_date = scheduled_draw_date + timedelta(weeks=1)
            
            update_game_query = "UPDATE game set start_date = %s, end_date = %s, scheduled_draw_date = %s where id = %s"
            cursor.execute(update_game_query, (start_date, end_date, scheduled_draw_date, game_id))
            conn.commit()
            
            # ---
                
            insert_draw_query = "INSERT INTO draw (game_id, created_at, draw_date) VALUES (%s, %s, %s)"
            values = (game_id, createAt, scheduled_draw_date)
            cursor.execute(insert_draw_query, values)
            conn.commit()
            cursor.close()
            conn.close()
            
            print("Draw inserted successfully.")
            
    except Exception as e:
        print('Une erreur s\'est produite lors l\'insetion du tirage : ' + str(e))
