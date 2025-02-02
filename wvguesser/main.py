
import sys
import json
import math
import time
import signal
import platform
import binascii
import subprocess
from typing import List
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Hash import CMAC


servers = []
excepted_j = [0, 1, 2, 4]
# excepted_j = list(range(5))
# excepted_j = list(range(8))

if platform.system() == 'Windows':
    MAIN_EXE = (Path(sys.argv[0]).parent / 'main.exe')
    if MAIN_EXE.exists() is False:
        MAIN_EXE = (Path('.').parent / 'main.exe')
    MAIN_EXE = MAIN_EXE.resolve().as_posix()
else:
    MAIN_EXE = (Path(sys.argv[0]).parent / 'main')
    if MAIN_EXE.exists() is False:
        MAIN_EXE = (Path('.').parent / 'main')
    MAIN_EXE = MAIN_EXE.resolve().as_posix()


def server_setup():
    for i in range(8):
        p = subprocess.Popen(f'"{MAIN_EXE}"', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        servers.append(p)


def handle_exit(signum, frame):
    close()


def close():
    try:
        [p.kill() for p in servers]
    except Exception:
        pass


def call_func(p: subprocess.Popen, msg: str):
    p.stdin.write(msg)
    p.stdin.flush()
    resp = p.stdout.readline()
    return resp.decode('utf-8').strip()


def multi_guessInput(bufs: List[str]):
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        results.extend(executor.map(guessInput, servers[:len(bufs)], bufs))
    return results


def guessInput(server, buf: bytes):
    return call_func(server, b'guessInput|' + buf + b'\n')


def getDeoaep(server, buf: bytes):
    return call_func(server, b'getDeoaep|' + buf + b'\n')


def run(hex_session_key: str):
    global excepted_j
    ts = time.time()
    encKey = binascii.a2b_hex(hex_session_key)
    print(hex_session_key)
    buf = [0] * 1026
    offset = 2
    while offset < 1026:
        print(f'[Progress] {(offset - 2) / 1024 * 100:.2f}% time used {time.time() - ts:.2f}s', end="\r")
        bt = math.floor((offset - 2) / 4)
        offs = math.floor((offset - 2) % 4)
        desired = (encKey[len(encKey) - bt - 1] >> (offs * 2)) & 3
        destail = hex_session_key[len(hex_session_key) - bt * 2:len(hex_session_key)]
        bufs = []
        j = buf[offset]
        if len(excepted_j) != 8 and offset + 8 > 1026:
            excepted_j = list(range(8))
        if offset + 8 < 1026:
            for _j in excepted_j:
                buf[offset] = _j
                bufs.append(binascii.b2a_hex(bytes(buf)))
            j = 7
            buf[offset] = 7
            results = list(multi_guessInput(bufs))
            for _j, val in zip(excepted_j, results):
                sub = int(val[len(val) - bt * 2 - 2:len(val) - bt * 2], 16)
                got = (sub >> (offs * 2)) & 3
                gtail = val[len(hex_session_key) - bt * 2:len(hex_session_key) + bt * 2]
                if got == desired and gtail == destail:
                    j = _j
                    buf[offset] = _j
                    break
                j = _j + 1
        else:
            while j < 8:
                buf[offset] = j
                st = binascii.b2a_hex(bytes(buf))
                val = guessInput(servers[0], st)
                sub = int(val[len(val) - bt * 2 - 2:len(val) - bt * 2], 16)
                got = (sub >> (offs * 2)) & 3
                gtail = val[len(hex_session_key) - bt * 2:len(hex_session_key) + bt * 2]
                if got == desired and gtail == destail:
                    break
                j += 1
        if j == 8:
            buf[offset] = 0
            offset -= 1
            if offset < 2:
                print('Could not match input')
                assert 1 == 0, "Could not find proper input encoding"
            buf[offset] += 1
            while buf[offset] == 8:
                buf[offset] = 0
                offset -= 1
                if offset < 2:
                    print('Could not match input')
                    assert 1 == 0, "Could not find proper input encoding"
                buf[offset] += 1
        else:
            offset += 1
    print(f'[Progress] 100% time used {time.time() - ts:.2f}s')
    outp = getDeoaep(servers[0], binascii.b2a_hex(bytes(buf)))
    print(f'clear session_key {outp}')
    if len(outp) < 10:
        print("Output", buf)
        assert 1 == 0, 'Could not remove padding, probably invalid key'
    return outp


def decrypt_license_keys(config_name: str, session_key: str, context_enc: str, key_infos: dict):
    cmac_obj = CMAC.new(binascii.a2b_hex(session_key), ciphermod=AES)
    cmac_obj.update(binascii.a2b_hex(context_enc))

    enc_cmac_key = cmac_obj.digest()
    lines = []
    for index, [keyId, keyData, keyIv] in key_infos.items():
        cipher = AES.new(enc_cmac_key, AES.MODE_CBC, iv=binascii.a2b_hex(keyIv))
        decrypted_key = cipher.decrypt(binascii.a2b_hex(keyData))
        # clear_key = Padding.unpad(decrypted_key, 16)
        print(f'{config_name} <id>:<k> {keyId}:{decrypted_key.hex()}')
        lines.append(f'{keyId}:{decrypted_key.hex()}')
    p = Path(f'wvkeys.txt')
    if p.exists() is False:
        p.touch()
    old_lines = p.read_text(encoding='utf-8')
    Path(f'wvkeys.txt').write_text('\n'.join(lines) + '\n' + old_lines, encoding='utf-8')


def main():
    server_setup()
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        path = (Path('.') / 'offline_config_7.json').resolve().as_posix()
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    clear_session_key = run(config['enc_session_key'])
    close()
    decrypt_license_keys(Path(path).name, clear_session_key, config['enc_key'], config['key_infos'])
    sys.stdin.read()


if __name__ == '__main__':
    main()