import socket
import struct
import time
from config import *

def send_base_frame(device_id=TEST_BASE_ID, rtcm_data=b'\xD3\x00'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost', TCP_BASE_PORT))
        print(f"已连接到基准站服务 {TCP_BASE_PORT}")
        
        frame = BASE_FRAME_HEADER + device_id + rtcm_data + BASE_FRAME_TAIL
        
        sock.sendall(frame)
        print(f"发送差分数据帧: {len(frame)} bytes")
        print(f"  帧头: {BASE_FRAME_HEADER.hex()}")
        print(f"  ID: {device_id.decode('ascii')}")
        print(f"  RTCM数据: {rtcm_data.hex()}")
        print(f"  帧尾: {BASE_FRAME_TAIL.hex()}")
        
        time.sleep(1)
    except Exception as e:
        print(f"基准站连接失败: {e}")
    finally:
        sock.close()

def send_mobile_position(device_id=TEST_MOBILE_ID, pos_type=0xE3, lat=34.26, lon=108.95):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost', TCP_MOBILE_PORT))
        print(f"已连接到移动站服务 {TCP_MOBILE_PORT}")
        
        pos_data = struct.pack('ddf', lon, lat, 0.0)
        frame = MOBILE_FRAME_HEADER + device_id + bytes([pos_type]) + pos_data + MOBILE_FRAME_TAIL
        
        sock.sendall(frame)
        print(f"发送坐标帧: {len(frame)} bytes")
        print(f"  帧头: {MOBILE_FRAME_HEADER.hex()}")
        print(f"  ID: {device_id.decode('ascii')}")
        print(f"  定位类型: 0x{pos_type:02X} ({POSITION_TYPES.get(pos_type, '未知')})")
        print(f"  坐标: ({lat}, {lon})")
        print(f"  帧尾: {MOBILE_FRAME_TAIL.hex()}")
        
        time.sleep(0.5)
    except Exception as e:
        print(f"移动站连接失败: {e}")
    finally:
        sock.close()

def send_mobile_nfc(device_id=TEST_MOBILE_ID, nfc_number="NFC00001"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost', TCP_MOBILE_PORT))
        print(f"已连接到移动站服务 {TCP_MOBILE_PORT}")
        
        timestamp = int(time.time() * 1000)
        timestamp_data = timestamp.to_bytes(10, 'big')
        nfc_data = nfc_number.encode('ascii').ljust(10)[:10]
        frame = MOBILE_FRAME_HEADER + device_id + timestamp_data + nfc_data + MOBILE_FRAME_TAIL
        
        sock.sendall(frame)
        print(f"发送NFC帧: {len(frame)} bytes")
        print(f"  帧头: {MOBILE_FRAME_HEADER.hex()}")
        print(f"  ID: {device_id.decode('ascii')}")
        print(f"  时间戳: {timestamp}")
        print(f"  NFC号码: {nfc_number}")
        print(f"  帧尾: {MOBILE_FRAME_TAIL.hex()}")
        
        time.sleep(0.5)
    except Exception as e:
        print(f"移动站连接失败: {e}")
    finally:
        sock.close()

def test_diff_data():
    print("\n=== 测试差分数据转发 ===")
    send_base_frame(BASE_STATION_A_ID)
    send_base_frame(BASE_STATION_B_ID)

def test_position_data():
    print("\n=== 测试坐标数据 ===")
    send_mobile_position(MOBILE_STATION_A_ID, 0x00, 34.260000, 108.950000)
    send_mobile_position(MOBILE_STATION_A_ID, 0xE1, 34.260010, 108.950010)
    send_mobile_position(MOBILE_STATION_A_ID, 0xE2, 34.260020, 108.950020)
    send_mobile_position(MOBILE_STATION_A_ID, 0xE3, 34.260030, 108.950030)

def test_nfc_data():
    print("\n=== 测试NFC数据 ===")
    send_mobile_nfc(MOBILE_STATION_A_ID, "NFC00001")
    send_mobile_nfc(MOBILE_STATION_A_ID, "NFC00002")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python test_client.py [base|position|nfc|test]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'base':
        device = sys.argv[2] if len(sys.argv) > 2 else 'A'
        device_id = BASE_STATION_A_ID if device == 'A' else BASE_STATION_B_ID
        send_base_frame(device_id)
    elif cmd == 'position':
        lat = float(sys.argv[2]) if len(sys.argv) > 2 else 34.26
        lon = float(sys.argv[3]) if len(sys.argv) > 3 else 108.95
        pos_type = int(sys.argv[4], 16) if len(sys.argv) > 4 else 0xE3
        send_mobile_position(TEST_MOBILE_ID, pos_type, lat, lon)
    elif cmd == 'nfc':
        nfc = sys.argv[2] if len(sys.argv) > 2 else "NFC00001"
        send_mobile_nfc(TEST_MOBILE_ID, nfc)
    elif cmd == 'test':
        test_diff_data()
        test_position_data()
        test_nfc_data()
        print("\n=== 测试完成 ===")
    else:
        print(f"未知命令: {cmd}")