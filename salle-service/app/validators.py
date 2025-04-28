from datetime import datetime

def validate_time_range(start_time, end_time):
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        return end > start
    except (ValueError, TypeError):
        return False

def validate_equipments(equipments):
    valid_equipments = {'video_projecteur', 'tableau_blanc', 'climatiseur', 'sonorisation'}
    return all(eq in valid_equipments for eq in equipments)