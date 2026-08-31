"""Deliberately bad code. Fixture for testing the quality-report skill.

Planted problems:
- process_data: complexity > 10, length > 50 lines, nesting > 4,
  and a comment that describes HOW instead of WHAT.
- build_report: 7 arguments.
- summarize_sales / summarize_refunds: duplicated >= 5-line block.
- legacy_export: dead (never called) and uses a bare except.
"""


def process_data(data):
    # Loop through the items, use nested ifs to inspect each field,
    # and append the transformed value to the results list.
    results = []
    for item in data:
        if item is not None:
            if isinstance(item, dict):
                if "value" in item:
                    if item["value"] > 0:
                        if item["value"] < 100:
                            results.append(item["value"] * 2)
                        else:
                            results.append(100)
                    else:
                        results.append(0)
                elif "name" in item:
                    if item["name"]:
                        results.append(len(item["name"]))
                    else:
                        results.append(-1)
                elif "flag" in item:
                    if item["flag"] is True:
                        results.append(1)
                    else:
                        results.append(0)
                else:
                    results.append(None)
            elif isinstance(item, list):
                if len(item) > 10:
                    results.append(sum(item[:10]))
                elif len(item) > 5:
                    results.append(sum(item[:5]))
                elif len(item) > 0:
                    results.append(item[0])
                else:
                    results.append(0)
            elif isinstance(item, str):
                if item.startswith("A"):
                    results.append(1)
                elif item.startswith("B"):
                    results.append(2)
                elif item.startswith("C"):
                    results.append(3)
                else:
                    results.append(0)
            elif isinstance(item, int):
                if item % 2 == 0:
                    results.append(item // 2)
                else:
                    results.append(item * 3 + 1)
            else:
                results.append(None)
    return results


def build_report(name, date, author, title, status, priority, category):
    """Build a report dictionary from its parts."""
    return {
        "name": name,
        "date": date,
        "author": author,
        "title": title,
        "status": status,
        "priority": priority,
        "category": category,
    }


def summarize_sales(records):
    """Return the average positive sale amount."""
    total = 0
    count = 0
    for record in records:
        if record["amount"] > 0:
            total += record["amount"]
            count += 1
    return total / count if count else 0


def summarize_refunds(records):
    """Return the average positive refund amount."""
    total = 0
    count = 0
    for record in records:
        if record["amount"] > 0:
            total += record["amount"]
            count += 1
    return total / count if count else 0


def legacy_export(records):
    """Export records as strings."""
    try:
        return [str(record) for record in records]
    except:
        return []


if __name__ == "__main__":
    sample = [{"value": 5}, [1, 2, 3], "Apple", 7, None]
    assert process_data(sample) == [10, 1, 1, 22]
    assert summarize_sales([{"amount": 10}, {"amount": -2}]) == 10
    assert summarize_refunds([{"amount": 4}, {"amount": 6}]) == 5
    print("fixture self-check ok")
