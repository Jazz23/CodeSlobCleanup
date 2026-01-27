inventory_data = []

def add_item(name, price, qty):
    global inventory_data
    item = {"name": name, "price": price, "qty": qty}
    inventory_data.append(item)

def calculate_total_value():
    total = 0
    for i in range(len(inventory_data)):
        item = inventory_data[i]
        p = item["price"]
        q = item["qty"]
        total = total + (p * q)
    return total

def find_duplicates():
    # O(n^2) search for duplicates
    dupes = []
    for i in range(len(inventory_data)):
        for j in range(len(inventory_data)):
            if i != j:
                if inventory_data[i]["name"] == inventory_data[j]["name"]:
                    # check if we already added it
                    found = False
                    for k in dupes:
                        if k == inventory_data[i]["name"]:
                            found = True
                    if not found:
                        dupes.append(inventory_data[i]["name"])
    return dupes

def process_orders(orders):
    # Messy logic with deep nesting
    for order in orders:
        for item_name in order["items"]:
            for inv_item in inventory_data:
                if inv_item["name"] == item_name:
                    if inv_item["qty"] > 0:
                        inv_item["qty"] = inv_item["qty"] - 1
                        print("Processed " + item_name)
                    else:
                        print("Out of stock: " + item_name)
