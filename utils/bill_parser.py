def validate_bill_data(bill_data: dict) -> tuple[bool, list]:

    errors = []

    if "items" not in bill_data or not isinstance(bill_data["items"], list):
        errors.append("Field 'items' tidak ditemukan atau bukan list")

    else:

        for i, item in enumerate(bill_data["items"]):

            required_fields = ["name", "quantity", "price_per_item", "total_price"]

            for field in required_fields:
                if field not in item:
                    errors.append(f"Item {i+1} tidak punya field '{field}'")

    if "subtotal" not in bill_data:
        errors.append("Field 'subtotal' tidak ditemukan")

    if "total" not in bill_data:
        errors.append("Field 'total' tidak ditemukan")

    is_valid = len(errors) == 0
    return is_valid, errors


def calculate_split(bill_data: dict, item_assignments: dict) -> dict:

    person_totals = {}

    items = bill_data.get("items", [])

    all_people = set()

    for people_list in item_assignments.values():
        all_people.update(people_list)

    for person in all_people:
        person_totals[person] = 0.0

    for item_idx, people_list in item_assignments.items():

        if item_idx >= len(items):
            continue

        item = items[item_idx]
        item_total = float(item.get("total_price", 0))

        num_people = len(people_list)

        if num_people == 0:
            continue

        portion = item_total / num_people

        for person in people_list:
            person_totals[person] += portion

    additional_charges = bill_data.get("additional_charges", [])

    total_additional = sum(
        float(charge.get("amount", 0)) for charge in additional_charges
    )

    if len(all_people) > 0 and total_additional > 0:
        additional_per_person = total_additional / len(all_people)

        for person in all_people:
            person_totals[person] += additional_per_person

    person_totals = {
        person: round(total, 2)
        for person, total in person_totals.items()
    }

    return person_totals


def format_currency(amount: float, currency: str = "IDR") -> str:

    if currency == "IDR":
        return f"Rp {amount:,.0f}".replace(",", ".")

    return f"{currency} {amount:,.2f}"