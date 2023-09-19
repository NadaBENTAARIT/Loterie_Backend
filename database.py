import mysql.connector


# ------------------------------ GAME -------------------------------------------------------------------------

def create_game_table(cursor):
    create_game_table_query = """
    CREATE TABLE IF NOT EXISTS game (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        game_type VARCHAR(255) CHECK (game_type IN ('GU', 'BD', 'BW')) NOT NULL,
        start_date DATETIME NOT NULL,
        end_date DATETIME NOT NULL,
        scheduled_draw_date DATETIME NOT NULL,
        prize_amount float NOT NULL,
        user_id VARCHAR(255) NOT NULL
    )
    """
    cursor.execute(create_game_table_query)
    print("Table 'game' created or already exists.")


# ------------------------------ DRAW -------------------------------------------------------------------------

def create_draw_table(cursor):
    create_draw_table_query = """
    CREATE TABLE IF NOT EXISTS draw (
        id INT PRIMARY KEY AUTO_INCREMENT,
        draw_date DATETIME NOT NULL,
        game_id INT, 
        created_at DATETIME ,
        updated_at DATETIME ,
        
        drawn_guarantee_number VARCHAR(255),
        
        drawn_ball_numbers VARCHAR(255),
        
        FOREIGN KEY (game_id) REFERENCES game(id) ON DELETE CASCADE  
    )
    """
    cursor.execute(create_draw_table_query)
    print("Table 'draw' created or already exists.")


# ------------------------------ TICKET  -------------------------------------------------------------------------

def create_ticket_table(cursor):
    create_ticket_table_query = """
    CREATE TABLE IF NOT EXISTS ticket (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ticket_guarantee_number VARCHAR(255),   
        ticket_ball_number VARCHAR(255),      
        `double` BOOLEAN NOT NULL,
        price FLOAT NOT NULL,
        state VARCHAR(255) CHECK (state IN ('active', 'désactivé', 'gagnant')) NOT NULL,
        purchase_date DATETIME NOT NULL,
        user_id VARCHAR(255) NOT NULL,
        user_phone VARCHAR(255) NOT NULL,
        draw_id INT,  
        FOREIGN KEY (draw_id) REFERENCES draw(id) ON DELETE CASCADE  
    )
    """
    cursor.execute(create_ticket_table_query)
    print("Table 'ticket' created or already exists.")



# ------------------------------ TICKET PRICE --------------------------------------------------------------------

def create_ticket_price_table(cursor):
    create_ticket_price_table_query = """
    CREATE TABLE IF NOT EXISTS ticket_price (
        id INT PRIMARY KEY AUTO_INCREMENT,
        price FLOAT NOT NULL,
        ticket_type VARCHAR(255) CHECK (ticket_type IN ('GU', 'BW', 'BD', 'D')) NOT NULL,
        start_date DATETIME NOT NULL,
        end_date DATETIME NOT NULL
    )
    """
    cursor.execute(create_ticket_price_table_query)
    print("Table 'ticket_price' created or already exists.")



# ------------------------------ PROVINCE ----------------------------------------------------------------------

def create_province_table(cursor):
    create_province_table_query = """
    CREATE TABLE IF NOT EXISTS province (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL
    )
    """
    cursor.execute(create_province_table_query)
    print("Table 'province' created or already exists.")


# ------------------------------ CITY ---------------------------------------------------------------------------

def create_city_table(cursor):
    create_city_table_query = """
    CREATE TABLE IF NOT EXISTS city (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        postal_code VARCHAR(255) NOT NULL,
        province_id INT,
        FOREIGN KEY (province_id) REFERENCES province(id) ON DELETE CASCADE
    )
    """
    cursor.execute(create_city_table_query)
    print("Table 'city' created or already exists.")


# ------------------------------ STREET -------------------------------------------------------------------------

def create_street_table(cursor):
    create_street_table_query = """
    CREATE TABLE IF NOT EXISTS street (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL,
        city_id INT,
        FOREIGN KEY (city_id) REFERENCES city(id) ON DELETE CASCADE
    )
    """
    cursor.execute(create_street_table_query)
    print("Table 'street' created or already exists.")


# ------------------------------ POINT OF SALE -------------------------------------------------------------------

def create_point_of_sale_table(cursor):
    create_point_of_sale_table_query = """
    CREATE TABLE IF NOT EXISTS point_of_sale (
        id INT PRIMARY KEY AUTO_INCREMENT,
        id_seller VARCHAR(255),
        name VARCHAR(255) NOT NULL,
        device_code VARCHAR(255) NOT NULL,
        fiscal_code VARCHAR(255) NOT NULL,
        street_id INT,
        FOREIGN KEY (street_id) REFERENCES street(id) ON DELETE CASCADE
    )
    """
    cursor.execute(create_point_of_sale_table_query)
    print("Table 'point_of_sale' created or already exists.")


def lambda_handler(event, context):
    try:
        conn = mysql.connector.connect(
            host='imperial.cgxxuuxgitss.af-south-1.rds.amazonaws.com',
            user='Imperial_23',
            password='Imperial_admin_2K23',
            database='loto',
            port=3306
        )

        if conn.is_connected():
            cursor = conn.cursor()

            # Test creation of game table
            create_game_table(cursor)

            # Test creation of draw table
            create_draw_table(cursor)

            # Test creation of ticket table
            create_ticket_table(cursor)

            # Test creation of ticket_price table
            create_ticket_price_table(cursor)

            # Test creation of province table
            create_province_table(cursor)

            # Test creation of city table
            create_city_table(cursor)

            # Test creation of street table
            create_street_table(cursor)

            # Test creation of point_of_sale table
            create_point_of_sale_table(cursor)

            conn.commit()

            cursor.close()
            conn.close()

            print("Table creation tests completed.")
            return "Table creation tests completed."
    except Exception as e:
        print("Error during table creation:", str(e))
        raise e


# Test the lambda_handler function
if __name__ == '__main__':
    lambda_handler(None, None)
