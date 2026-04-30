import struct
from config import *

def parse_device_id(device_id):
    if len(device_id) != 6:
        return None
    
    id_str = device_id.decode('ascii', errors='ignore')
    
    if len(id_str) != 6:
        return None
    
    device_type = id_str[0]
    zone = id_str[1:3]
    number = id_str[3:6]
    
    return {
        'device_type': device_type,
        'zone': zone,
        'number': number,
        'type_name': '基准站' if device_type == ID_TYPE_BASE else '移动站',
        'id_str': id_str
    }

def is_base_frame(data):
    return len(data) >= BASE_FRAME_MIN_LEN and data.startswith(BASE_FRAME_HEADER) and data.endswith(BASE_FRAME_TAIL)

def is_mobile_frame(data):
    return len(data) >= 10 and data.startswith(MOBILE_FRAME_HEADER)

def parse_base_frame(data):
    if not is_base_frame(data):
        return None
    
    header = data[:2]
    device_id = data[2:8]
    rtcm_data = data[8:-2]
    tail = data[-2:]
    
    return {
        'type': 'base',
        'header': header,
        'device_id': device_id,
        'device_info': parse_device_id(device_id),
        'rtcm_data': rtcm_data,
        'tail': tail,
        'raw_data': data
    }

def parse_mobile_frame(data):
    if not is_mobile_frame(data):
        return None
    
    header = data[:2]
    device_id = data[2:8]
    
    if len(data) >= MOBILE_POS_FRAME_LEN and data.endswith(MOBILE_FRAME_TAIL):
        pos_type = data[8]
        if pos_type in POSITION_TYPES:
            pos_data = data[9:29]
            tail = data[-2:]
            
            lon = struct.unpack('d', pos_data[:8])[0]
            lat = struct.unpack('d', pos_data[8:16])[0]
            alt = struct.unpack('f', pos_data[16:20])[0] if len(pos_data) >= 20 else 0.0
            
            return {
                'type': 'position',
                'header': header,
                'device_id': device_id,
                'device_info': parse_device_id(device_id),
                'position_type': pos_type,
                'position_type_name': POSITION_TYPES.get(pos_type, '未知'),
                'lon': lon,
                'lat': lat,
                'alt': alt,
                'raw_pos_data': pos_data,
                'tail': tail,
                'raw_data': data
            }
    
    if len(data) >= MOBILE_NFC_FRAME_LEN and data.endswith(MOBILE_FRAME_TAIL):
        timestamp_data = data[8:18]
        nfc_number = data[18:28]
        tail = data[-2:]
        
        try:
            timestamp = int.from_bytes(timestamp_data, 'big')
        except:
            timestamp = 0
        
        return {
            'type': 'nfc',
            'header': header,
            'device_id': device_id,
            'device_info': parse_device_id(device_id),
            'timestamp': timestamp,
            'nfc_number': nfc_number.decode('ascii', errors='ignore').strip(),
            'tail': tail,
            'raw_data': data
        }
    
    return None

def build_base_frame(device_id, rtcm_data):
    return BASE_FRAME_HEADER + device_id + rtcm_data + BASE_FRAME_TAIL

def build_mobile_position_frame(device_id, pos_type, lon, lat, alt=0.0):
    pos_data = struct.pack('ddf', lon, lat, alt)
    return MOBILE_FRAME_HEADER + device_id + bytes([pos_type]) + pos_data + MOBILE_FRAME_TAIL

def build_mobile_nfc_frame(device_id, timestamp, nfc_number):
    timestamp_data = timestamp.to_bytes(10, 'big')
    nfc_data = nfc_number.encode('ascii').ljust(10)[:10]
    return MOBILE_FRAME_HEADER + device_id + timestamp_data + nfc_data + MOBILE_FRAME_TAIL

def validate_checksum(data):
    return True