import asyncio
import socket

from random import randint

from zeroconf import ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf

import zmq
import zmq.asyncio


def on_service_state_change(state_change_callback):
    async def async_fx(zeroconf: Zeroconf, service_type, name, state_change):
        info = await zeroconf.async_get_service_info(service_type, name)
        if state_change_callback is not None:
            await state_change_callback(service_type, name, state_change, info)

    def fx(zeroconf, service_type, name, state_change):
        asyncio.ensure_future(async_fx(zeroconf, service_type, name, state_change))
    
    return fx

async def zeroconf_init(service_info, service_type, state_change_callback):
    zeroconf = AsyncZeroconf()

    await zeroconf.async_register_service(service_info)

    browser = AsyncServiceBrowser(zeroconf.zeroconf, [service_type], handlers=[on_service_state_change(state_change_callback)])
    
    return zeroconf


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(("10.254.254.254", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


async def forward_message(base_port, transform=None):
    context = zmq.asyncio.Context()
    rep_socket = context.socket(zmq.PULL)
    rep_socket.bind(f"tcp://*:{base_port}")
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind(f"tcp://*:{base_port+1}")
    pub_socket.setsockopt(zmq.LINGER, 1)

    while True:
        message = await rep_socket.recv()
        if transform is not None:
            message = transform(message)
        await pub_socket.send(message)


async def subscriber(socket, action):
    while True:
        try:
            message = await socket.recv_string(flags=zmq.NOBLOCK)
            await action(message)
        except zmq.error.Again as e:
            await asyncio.sleep(0.1)


async def init(
    clan, subscriber_action, statusbar_callback=None, transform=None, base_port=None
):
    # zeromq section
    zmq_context = zmq.asyncio.Context()
    push_socket = zmq_context.socket(zmq.PUSH)
    sub_socket = zmq_context.socket(zmq.SUB)
    
    if base_port is None:
        base_port = randint(8000, 8999)

    # zeroconf section
    services_seen = {}
    service_type = f"_{clan}._http._tcp.local."

    ws_info = AsyncServiceInfo(
        service_type,
        f"{get_ip()}_{base_port}._{clan}._http._tcp.local.",
        base_port,
        0,
        0,
        addresses=[get_ip()],
    )
        
    async def state_callback(service_type, name, state_change, info):
        if state_change == ServiceStateChange.Added or state_change == ServiceStateChange.Updated:
            services_seen[name] = info
        elif state_change == ServiceStateChange.Removed:
            del services_seen[name]
            
        host = min(
            [
                (info.parsed_addresses()[0], int(info.port))
                for info in services_seen.values()
            ],
            default=("localhost", 8080),
        )
        base_host = f"tcp://{host[0]}:{host[1]}"
    
        if statusbar_callback is not None:
            await statusbar_callback(base_host)

        push_socket.connect(base_host)
        sub_socket.connect(f"tcp://{host[0]}:{host[1]+1}")
        sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")                
    
    zeroconf = await zeroconf_init(ws_info, service_type, state_callback)

    # background tasks: forwarder, and subscriber
    asyncio.create_task(forward_message(base_port, transform))
    asyncio.create_task(subscriber(sub_socket, subscriber_action))

    async def send_string(msg):
        push_socket.send_string(msg)
    
    async def lib_deinit():
        await zeroconf.async_unregister_service(ws_info)
        await zeroconf.async_close()

    return send_string, lib_deinit
