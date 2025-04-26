from datetime import datetime, timedelta

def calculate_next_run(recurrence: str):
    now = datetime.utcnow()
    if recurrence == "daily":
        return now + timedelta(days=1)
    elif recurrence == "weekly":
        return now + timedelta(weeks=1)
    elif recurrence == "monthly":
        return now + timedelta(days=30)  # Simplified
    elif recurrence == "every_2_days":
        return now + timedelta(days=2)
    else:
        raise ValueError("Invalid recurrence type")
