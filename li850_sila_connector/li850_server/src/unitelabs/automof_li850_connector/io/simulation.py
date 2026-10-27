from unitelabs.bus.testing import stub_maker

DEVICE_DATA: dict[bytes, bytes] = {
    b"status": b"ok",
    b"getSerial\r": b"0000012345\r\n"
}

stubs = [stub_maker(k, v) for k, v in DEVICE_DATA.items()]