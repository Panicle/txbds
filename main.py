import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import json
import os

from config import *
from protocol import parse_base_frame, parse_mobile_frame
from storage import init_db, save_coordinate, save_nfc_record, get_recent_coordinates, get_nfc_records, get_shoe_by_nfc, add_shoe_mapping

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="智能铁鞋服务端", version="1.0")

os.makedirs("web", exist_ok=True)
app.mount("/web", StaticFiles(directory="web", html=True), name="web")

websocket_clients = set()

base_connections = {}
mobile_connections = {}

async def handle_base_connection(reader, writer):
    addr = writer.get_extra_info('peername')
    logger.info(f"基准站连接: {addr}")
    
    buffer = b''
    device_id = None
    
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            
            buffer += data
            
            while len(buffer) >= BASE_FRAME_MIN_LEN:
                if buffer.startswith(BASE_FRAME_HEADER):
                    tail_pos = buffer.find(BASE_FRAME_TAIL)
                    if tail_pos != -1:
                        frame_data = buffer[:tail_pos + 2]
                        buffer = buffer[tail_pos + 2:]
                        
                        frame = parse_base_frame(frame_data)
                        if frame:
                            device_id = frame['device_id']
                            device_id_str = device_id.decode('ascii', errors='ignore')
                            base_connections[device_id_str] = writer
                            logger.info(f"基准站注册: {device_id_str}")
                            
                            if device_id_str in DEVICE_PAIRS:
                                mobile_id_str = DEVICE_PAIRS[device_id_str]
                                if mobile_id_str in mobile_connections:
                                    mobile_writer = mobile_connections[mobile_id_str]
                                    try:
                                        mobile_writer.write(frame_data)
                                        await mobile_writer.drain()
                                        logger.info(f"差分数据转发成功: {device_id_str} -> {mobile_id_str}")
                                    except Exception as e:
                                        logger.error(f"差分数据转发失败: {e}")
                                else:
                                    logger.info(f"差分数据未转发: 配对移动站离线 {mobile_id_str}")
                            else:
                                logger.info(f"差分数据未转发: 无配对关系 {device_id_str}")
                    else:
                        break
                else:
                    buffer = buffer[1:]
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"基准站连接错误: {e}")
    finally:
        if device_id:
            device_id_str = device_id.decode('ascii', errors='ignore')
            if device_id_str in base_connections:
                del base_connections[device_id_str]
                logger.info(f"基准站注销: {device_id_str}")
        writer.close()
        await writer.wait_closed()
        logger.info(f"基准站断开: {addr}")

async def handle_mobile_connection(reader, writer):
    addr = writer.get_extra_info('peername')
    logger.info(f"移动站连接: {addr}")
    
    buffer = b''
    device_id = None
    
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            
            buffer += data
            
            while len(buffer) >= MOBILE_NFC_FRAME_LEN:
                if buffer.startswith(MOBILE_FRAME_HEADER):
                    tail_pos = buffer.find(MOBILE_FRAME_TAIL)
                    if tail_pos != -1:
                        frame_data = buffer[:tail_pos + 2]
                        buffer = buffer[tail_pos + 2:]
                        
                        frame = parse_mobile_frame(frame_data)
                        if frame:
                            device_id = frame['device_id']
                            device_id_str = device_id.decode('ascii', errors='ignore')
                            mobile_connections[device_id_str] = writer
                            logger.info(f"移动站注册: {device_id_str}")
                            
                            if frame['type'] == 'position':
                                record_id = save_coordinate(frame)
                                logger.info(f"坐标记录: {frame['device_info']['id_str']} - "
                                            f"{frame['position_type_name']} "
                                            f"({frame['lat']:.6f}, {frame['lon']:.6f})")
                                
                                await broadcast_position(frame)
                            elif frame['type'] == 'nfc':
                                record_id = save_nfc_record(frame)
                                logger.info(f"NFC记录: {frame['device_info']['id_str']} - "
                                            f"{frame['nfc_number']}")
                    else:
                        break
                else:
                    buffer = buffer[1:]
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"移动站连接错误: {e}")
    finally:
        if device_id:
            device_id_str = device_id.decode('ascii', errors='ignore')
            if device_id_str in mobile_connections:
                del mobile_connections[device_id_str]
                logger.info(f"移动站注销: {device_id_str}")
        writer.close()
        await writer.wait_closed()
        logger.info(f"移动站断开: {addr}")

async def broadcast_position(frame):
    if not websocket_clients:
        logger.info("WebSocket广播: 无客户端连接")
        return
    
    position_data = {
        'type': 'position',
        'device_id': frame['device_id'].decode('ascii', errors='ignore'),
        'device_type': frame['device_info']['device_type'],
        'position_type': frame['position_type'],
        'position_type_name': frame['position_type_name'],
        'lat': frame['lat'],
        'lon': frame['lon'],
        'alt': frame['alt'],
        'receive_time': frame.get('receive_time', '')
    }
    
    message = json.dumps(position_data)
    logger.info(f"WebSocket广播: {len(websocket_clients)} 个客户端")
    
    disconnected = []
    
    for client in websocket_clients:
        try:
            await client.send_text(message)
        except Exception as e:
            logger.error(f"WebSocket广播失败: {e}")
            disconnected.append(client)
    
    for client in disconnected:
        websocket_clients.remove(client)

@app.get("/")
async def root():
    return RedirectResponse(url="/web/")

@app.get("/api/coords")
async def get_coordinates(limit: int = 100):
    coords = get_recent_coordinates(limit)
    for c in coords:
        c.pop('raw_data', None)
        c.pop('id', None)
    return coords

@app.get("/api/nfc")
async def get_nfc(limit: int = 100):
    records = get_nfc_records(limit)
    for r in records:
        r.pop('raw_data', None)
        r.pop('id', None)
    return records

@app.get("/api/shoe/{nfc_number}")
async def get_shoe(nfc_number: str):
    shoe = get_shoe_by_nfc(nfc_number)
    if shoe:
        shoe.pop('id', None)
    return shoe

class ShoeMapping(BaseModel):
    nfc_number: str
    shoe_name: str
    shoe_code: str

@app.post("/api/shoe")
async def add_shoe(mapping: ShoeMapping):
    success = add_shoe_mapping(mapping.nfc_number, mapping.shoe_name, mapping.shoe_code)
    return {"success": success}

@app.get("/api/devices")
async def get_devices():
    return {
        'base_stations': list(base_connections.keys()),
        'mobile_stations': list(mobile_connections.keys())
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.add(websocket)
    logger.info(f"WebSocket客户端连接: {len(websocket_clients)} 个客户端")
    
    try:
        recent_coords = get_recent_coordinates(10)
        for coord in recent_coords:
            coord.pop('raw_data', None)
            coord.pop('id', None)
        
        await websocket.send_text(json.dumps({'type': 'history', 'data': recent_coords}))
        
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)
        logger.info(f"WebSocket客户端断开: {len(websocket_clients)} 个客户端")
    except Exception as e:
        websocket_clients.remove(websocket)
        logger.error(f"WebSocket错误: {e}")

async def start_tcp_servers():
    base_server = await asyncio.start_server(
        handle_base_connection, '0.0.0.0', TCP_BASE_PORT
    )
    
    mobile_server = await asyncio.start_server(
        handle_mobile_connection, '0.0.0.0', TCP_MOBILE_PORT
    )
    
    logger.info(f"基准站TCP服务启动: 0.0.0.0:{TCP_BASE_PORT}")
    logger.info(f"移动站TCP服务启动: 0.0.0.0:{TCP_MOBILE_PORT}")
    
    async with base_server, mobile_server:
        await asyncio.gather(
            base_server.serve_forever(),
            mobile_server.serve_forever()
        )

if __name__ == '__main__':
    import uvicorn
    from uvicorn.config import Config
    from uvicorn.server import Server
    
    web_port = int(os.environ.get('PORT', WEB_PORT))
    
    config = Config(app=app, host="0.0.0.0", port=web_port)
    server = Server(config)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    init_db()
    
    loop.create_task(start_tcp_servers())
    
    loop.run_until_complete(server.serve())