"""Synchronous read-only Modbus TCP client."""
from __future__ import annotations
from dataclasses import dataclass
import logging, time
from threading import Lock
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from .const import REGISTER_CHUNK_SIZE, REGISTER_END, REGISTER_START, VALIDATION_REGISTER_COUNT, VALIDATION_REGISTER_START
_LOGGER=logging.getLogger(__name__)
class AutarcoConnectionError(Exception):
    """Communication error."""
@dataclass(slots=True, frozen=True)
class AutarcoConnectionSettings:
    host:str; port:int; device_id:int; timeout:int; retries:int=2
@dataclass(slots=True, frozen=True)
class AutarcoReadResult:
    registers:dict[int,int]; response_ms:float; attempts:int; unsupported_blocks:tuple[str,...]
class AutarcoModbusClient:
    def __init__(self, settings:AutarcoConnectionSettings)->None:
        self._settings=settings; self._lock=Lock()
    def _client(self)->ModbusTcpClient:
        return ModbusTcpClient(self._settings.host, port=self._settings.port, timeout=self._settings.timeout, retries=1)
    def validate(self)->None:
        with self._lock:
            client=self._client()
            try:
                if not client.connect(): raise AutarcoConnectionError(f"Geen verbinding met {self._settings.host}:{self._settings.port}")
                result=client.read_input_registers(VALIDATION_REGISTER_START,count=VALIDATION_REGISTER_COUNT,device_id=self._settings.device_id)
                if result.isError(): raise AutarcoConnectionError(f"Modbus-validatiefout: {result}")
                if not getattr(result,'registers',None): raise AutarcoConnectionError('Geen registerwaarden ontvangen')
            except AutarcoConnectionError: raise
            except (ModbusException,OSError) as err: raise AutarcoConnectionError(str(err)) from err
            finally: client.close()
    def read_all(self)->AutarcoReadResult:
        with self._lock:
            started=time.monotonic(); last=None
            for attempt in range(1,self._settings.retries+2):
                try:
                    regs,unsupported=self._read_once()
                    return AutarcoReadResult(regs,round((time.monotonic()-started)*1000,1),attempt,tuple(unsupported))
                except AutarcoConnectionError as err:
                    last=err
                    if attempt<=self._settings.retries: time.sleep(min(.5*attempt,2))
            raise AutarcoConnectionError(str(last) if last else 'Onbekende communicatiefout')
    def _read_once(self)->tuple[dict[int,int],list[str]]:
        client=self._client(); regs={}; unsupported=[]
        try:
            if not client.connect(): raise AutarcoConnectionError(f"Geen verbinding met {self._settings.host}:{self._settings.port}")
            start=REGISTER_START
            while start<=REGISTER_END:
                count=min(REGISTER_CHUNK_SIZE,REGISTER_END-start+1); end=start+count-1
                try: result=client.read_input_registers(start,count=count,device_id=self._settings.device_id)
                except (ModbusException,OSError) as err: raise AutarcoConnectionError(f"Leesfout {start}-{end}: {err}") from err
                if result.isError(): unsupported.append(f"{start}-{end}")
                else:
                    for offset,value in enumerate((getattr(result,'registers',None) or [])[:count]): regs[start+offset]=int(value)
                start+=count
        finally: client.close()
        if not regs: raise AutarcoConnectionError('Geen registers gelezen')
        return regs,unsupported
