from microbit import *
from microbit import i2c
from array import array

# ---------------------------------mb---------------------------
_rmo = False
_sho = 1
_typ = None
_res = []
_map = lambda x: 22 + x + 26 * (x > 1)
_tt = array('B', (0,) * 16)


def remote_on(short=1):
    global mb_radio, _rmo, r_eval, _sho
    _rmo = True
    _sho = short
    import mb_radio, radio
    radio.on()
    radio.config(length=64)
    r_eval = mb_radio.r_eval


def _exe(s, b, l, r):
    try:
        i2c.write(s, b)
        if l:
            d = i2c.read(s, l)
            if not r:
                d = int.from_bytes(d, 'big')
            return d
    except:
        pass


def command(slot, bseq, size=0, raw=False):
    if isinstance(slot, tuple):
        return mb_radio.send(slot[0], bseq, size, not raw)
    if slot is None:
        _res.clear()
        flag = 0
        for i in range(16):
            if _tt[i] == _typ:
                rr = _exe(_map(i), bseq, size, raw)
                if rr is not None: _res.append(rr)
                flag = 1
        if _rmo and not (flag and _sho):
            rr = command((_typ,), bseq, size, raw)
            if rr != None:
                if isinstance(rr, tuple):
                    _res.extend(rr)
                else:
                    _res.append(rr)
        if not _res: return None
        return _res[0] if len(_res) == 1 else tuple(_res)
    return _exe(slot, bseq, size, raw)


def get_state(addr):
    return command(slot(addr), b'get_state', 1)


def get_type(addr):
    t = slot(addr)
    n = t - 22 - 26 * (t > 23)
    return _tt[n]


def get_id(addr):
    raw = _exe(slot(addr), b'get_id', 16, 1)
    return raw and '%08x' % int.from_bytes(raw[:4], 'little')


def slot(addr, type=None):
    global _typ
    if isinstance(addr, int) or addr == None:
        if addr == None:
            _typ = type
        return addr
    addr = addr.lower()
    if len(addr) < 8:
        addr = addr[-1].lower()
        if 'a' <= addr <= 'p':
            return _map(ord(addr) - 97)
    for i in range(16):
        tmp = _map(i)
        if _tt[i] > 0 and get_id(tmp) == addr: return tmp
    if _rmo: return (addr,)


def get_bin():
    tmp = i2c.read(32, 1)[0]
    res, ptr = '', 1
    for i in range(8):
        res += str(int(tmp & ptr > 0))
        ptr *= 2
    return res


def refresh(p):
    _tt[p] = _exe(_map(p), b'get_type', 1, 0) or 0


for p in range(16):
    _tt[p] = _exe(_map(p), b'get_type', 1, 0) or 0


# ----------------------joypad----------------------------

# 改成-8 -- 8 的手柄坐标了
def conv(data):
    x, y = data[5] + data[6] // 256, data[7] + data[8] // 256
    x = x - 8
    y = 8 - y
    return tuple(data[:5]), (x, y)


def values(addr=None):
    data = command(slot(addr, 7), b'get_key_val', 9, True)
    if isinstance(data, bytes):
        return data
    if data == None:
        return None
    # return tuple(conv(i) for i in data)


def keys(addr=None):
    return values(addr)[0]


def stickxy(addr=None):
    return values(addr)[1]


uart.init(baudrate=19200)

while not (button_a.get_presses() + button_b.get_presses()):
    data1 = values(22)
    data2 = values(23)
    uart.write(data1 + bytes([9]) + data2 + b'\n')  # sep = 9!!!
    display.show(Image.ANGRY)
    sleep(20)
display.scroll("OVER!")
display.clear()
