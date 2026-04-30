import os

# 设备ID配置
BASE_STATION_A_ID = b'100101'
BASE_STATION_B_ID = b'100102'
MOBILE_STATION_A_ID = b'200101'
MOBILE_STATION_B_ID = b'200102'

TEST_BASE_ID = BASE_STATION_A_ID
TEST_MOBILE_ID = MOBILE_STATION_A_ID

# 端口配置
TCP_BASE_PORT = 8001
TCP_MOBILE_PORT = 8002
WEB_PORT = 8080

# 数据存储
DATA_DIR = os.environ.get('DATA_DIR', "data")
DB_PATH = os.path.join(DATA_DIR, "smart_shoe.db")

# 帧格式配置
BASE_FRAME_HEADER = b'\x55\xAA'
MOBILE_FRAME_HEADER = b'\xAA\x55'
BASE_FRAME_TAIL = b'\xAA\x55'
MOBILE_FRAME_TAIL = b'\x55\xAA'

# 定位类型定义
POSITION_TYPES = {
    0x00: '人员定位',
    0xE1: '铁鞋初步定位',
    0xE2: '铁鞋改正后定位',
    0xE3: '铁鞋精密定位'
}

# ID类型定义
ID_TYPE_BASE = '1'
ID_TYPE_MOBILE = '2'

# 帧长度配置
BASE_FRAME_MIN_LEN = 10
MOBILE_POS_FRAME_LEN = 31
MOBILE_NFC_FRAME_LEN = 30

# 配对关系（基准站ID → 移动站ID）
DEVICE_PAIRS = {
    BASE_STATION_A_ID.decode('ascii'): MOBILE_STATION_A_ID.decode('ascii'),
    BASE_STATION_B_ID.decode('ascii'): MOBILE_STATION_B_ID.decode('ascii')
}