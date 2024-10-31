from device import Device
from adapter.adapter import InstructionAdapter
from builder import Builder

device = Device()
adapter = InstructionAdapter(device)
builder = Builder(device)

builder.build()