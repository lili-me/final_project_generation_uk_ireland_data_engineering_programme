
""" This module has functions to insert into: 
items table, locations table, transaction-items table and transaction table. 
This module has function to check if entries are duplicate.
"""

# takes unique location names and inserts into locations table
def insert_into_location_table(connection, unique_location_list):
    try:
        cursor = connection.cursor()

        # depends if the column is a dictionary in a list
        for location_name in unique_location_list:
            
            if check_if_duplicate_entry(connection, 'locations', location_name, 'location_name'):
                continue    # checks if entries already there, if it finds, it ignores the duplicates 
            else:
                insert_location_to_db = ''' INSERT INTO locations(location_name)
                VALUES (%s);
                '''  #it inserts non-duplicate entries

                # we need to make tuple to be able to execute the cursor on postgres!
                cursor.execute(insert_location_to_db, (location_name,)) 
                connection.commit()

        cursor.close()

    except Exception as e:
        print(f'Failed to open connection: {e}')

# takes items and inserts into items table
def insert_into_item_table(connection, items_list):
    try:
        cursor = connection.cursor()

        # Looping each item in the item list
        for item in items_list:
            sql = "SELECT * FROM items WHERE item_name = '" + item['item_name'] + "' AND item_price = '" + str(item['item_price']) + "' LIMIT (1);"
            cursor.execute(sql)
            if cursor.fetchone():
                continue  # checks if entries already there, if it finds, it ignores the duplicates 
            else:
                insert_item_to_db = ''' INSERT INTO items(item_name, item_price)
                VALUES (%s, %s);
                ''' #it inserts non-duplicate entries

                # assuming the key names in a dictionary is item_name  and item_price
                item_values = (item['item_name'], item['item_price'])
                
                cursor.execute(insert_item_to_db, item_values)
                connection.commit()

        cursor.close()

    except Exception as e:
        print(f'Failed to open connection: {e}')

# checks the database table if there is a similar entry before inserting
def check_if_duplicate_entry(connection, table: str, entry: str, column_name: str):
    try:
        cursor = connection.cursor()

        sql = "SELECT * FROM " + table + " WHERE " + column_name + " = " + f"'{entry}'" + " LIMIT (1)"
        
        cursor.execute(sql)

        if cursor.fetchone():
            return True
        else:
            return False
        
    except Exception as e:
        print(f'Failed to open connection: {e}')
    
def insert_into_transactions_table(connection, transactions, items):
    try:
        cursor = connection.cursor()

        # Looping each entry in the transaction list
        for transaction in transactions:

            location_name = transaction['location']
            sql_location = "SELECT location_id FROM locations WHERE location_name = " + f"'{location_name}'" + " LIMIT (1)"
            cursor.execute(sql_location)
            location_id = cursor.fetchone()[0]

            payment_method = transaction['payment_method']
            sql_payment = "SELECT payment_id FROM payment_types WHERE payment = " + f"'{payment_method}'" + " LIMIT (1)"
            cursor.execute(sql_payment)
            payment_id = cursor.fetchone()[0]

            # has own check if duplicate since multiple values needed to verify match
            sql = "SELECT * FROM transactions WHERE date_time = '" + transaction['date_time'] + "' AND location_id = '" + str(location_id) + "' AND total_price = '" + transaction['total_price'] + "' LIMIT (1)"
            cursor.execute(sql)
            if cursor.fetchone():
                continue
            else:
                insert_transaction_to_db = ''' INSERT INTO transactions(date_time, location_id, total_price, payment_id)
                VALUES (%s, %s, %s, %s);
                '''
                transaction_data = (transaction['date_time'], location_id, transaction['total_price'], payment_id)
                cursor.execute(insert_transaction_to_db, transaction_data)

                get_transaction_id = "SELECT transaction_id FROM transactions WHERE date_time = '" + transaction['date_time'] + "' AND location_id = '" + str(location_id) + "' AND total_price = '" + transaction['total_price'] + "' LIMIT (1)"
                cursor.execute(get_transaction_id)
                transaction_id = cursor.fetchone()[0]
                
                insert_into_transaction_items_table(connection, transaction_id, transaction['temp_transaction_id'], items)

            connection.commit()

        cursor.close()

    except Exception as e:
        print(f'Failed to open connection: {e}')

# WIP - issue to be solved: getting different items unrelated to the transaction
def insert_into_transaction_items_table(connection, transaction_id, temp_transaction, items):
    try:
        cursor = connection.cursor()

        for item in items:
            if item['temp_transaction_id'] == temp_transaction:
                item_name = item['item_name']
                sql_item = "SELECT item_id FROM items WHERE item_name = " + f"'{item_name}'" + " LIMIT (1)"

                cursor.execute(sql_item)
                item_id = cursor.fetchone()[0]

                insert_transaction_item_to_db = """INSERT INTO transaction_items(transaction_id, item_id)
                VALUES (%s, %s);"""

                transaction_item_data = (transaction_id, item_id)

                cursor.execute(insert_transaction_item_to_db, transaction_item_data)

            connection.commit()

        cursor.close()

    except Exception as e:
        print(f'Failed to open connection: {e}')


if __name__ == '__main__':
    import extract_transform as et
    from create_database import setup_db_connection 

    connection = setup_db_connection()

    transactions = et.read_csv_to_list("data/chesterfield_25-08-2021_09-00-00.csv")

    sensitive_data = ["customer_name", "card_number"]
    et.remove_sensitive_data(transactions, sensitive_data)

    items = et.create_item_list(transactions)

    transactions = et.convert_all_dates(transactions, ['date_time'])

    unique_items = et.get_unique_items(items)
    unique_locations = et.get_unique_locations(transactions)

    # insert_into_item_table(connection, unique_items)
    # insert_into_location_table(connection, unique_locations)

    # transaction_id = 0
    # for i, transaction in enumerate(transactions):
    #     if i == 0:
    #         print(transaction)
    #         for item in items:
    #             if item['temp_transaction_id'] == transaction['temp_transaction_id']:
    #                 print(item)
    #         insert_into_transaction_items_table(connection, transaction_id, transaction['temp_transaction_id'], items)

