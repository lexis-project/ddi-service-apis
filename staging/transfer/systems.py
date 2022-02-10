import yaml
"""
This module exposes systems and encryption variables.
"""

systems = {}
encryption = {}
with open("/etc/staging_api/system.yml") as file:
    systems = yaml.load(file, Loader=yaml.FullLoader)
    encryption = systems["encryption"]


def get_burst_buffer_path():
    return systems['systems'][systems['burst_buffer_area']]['base_path']


def find_system_by_zone(zone):
    for sys_name, sys_config in systems['systems'].items():
        if sys_config['type'] == 'iRODS' and sys_config['zone'] == zone:
            return (sys_name, sys_config)
    return False
