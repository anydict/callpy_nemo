from typing import Union


def fix_iso_timestamp(var_time: Union[str, None]):
    """ Converting the date to the correct string format """

    if isinstance(var_time, str) and '+' in var_time:
        # 2023-05-16T00:33:52.951+0300 to 2023-05-16T00:33:52.951000
        return f'{var_time[:23]}000'
    elif isinstance(var_time, str) and len(var_time) == 26 and 'T' not in var_time:
        # 2023-05-16 00:33:52.951+0300 to 2023-05-16T00:33:52.951000
        return var_time.replace(' ', 'T')
    elif isinstance(var_time, str) and len(var_time) == 26 and 'T' in var_time:
        # if correct return raw
        return var_time
    else:
        # if invalid return empty string
        return ''
