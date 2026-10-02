import re


def generate_id(model_cls, field_name, prefix):
    """
    Generates the next sequential ID for a model, e.g. CUS00001, CUS00002...
    prefix: 3-letter code (e.g. 'CUS', 'RES', 'ORD')
    field_name: name of the CHAR(8) primary key field on the model
    """
    last_obj = model_cls.objects.order_by(f'-{field_name}').first()
    if last_obj:
        last_value = getattr(last_obj, field_name)
        match = re.search(r'(\d+)$', last_value)
        next_num = int(match.group(1)) + 1 if match else 1
    else:
        next_num = 1
    return f"{prefix}{next_num:05d}"