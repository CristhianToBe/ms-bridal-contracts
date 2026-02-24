def blank_leaves(obj):
    if isinstance(obj, dict):
        return {key: blank_leaves(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [blank_leaves(value) for value in obj]
    return ""
