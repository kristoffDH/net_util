import socket
import argparse
import csv
import sys


def is_tcp_port_open(host, port, timeout=1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
    except (socket.timeout, socket.error):
        return False
    finally:
        sock.close()
    return True


def tcp_client(host, port, use_file, file_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    if use_file:
        with open(file_path, 'r') as file:
            for line in file:
                sock.sendall(line.encode())
                response = sock.recv(4096)
                print("Received:", response.decode())
    else:
        try:
            while True:
                data = input("Enter message: ")
                sock.sendall(data.encode())
                response = sock.recv(4096)
                print("Received:", response.decode())
        except socket.error as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("Client exiting...")

    sock.close()


def udp_client(host, port, use_file, file_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if use_file:
        with open(file_path, 'r') as file:
            for line in file:
                sock.sendto(line.encode(), (host, port))
                response, _ = sock.recvfrom(4096)
                print("Received:", response.decode())
    else:
        try:
            while True:
                data = input("Enter message: ")
                sock.sendto(data.encode(), (host, port))
                response, _ = sock.recvfrom(4096)
                print("Received:", response.decode())
        except socket.error as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("Client exiting...")

    sock.close()


def parse_csv(file_path):
    responses = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            index, dtype, value = row
            if dtype == "hex":
                responses.append(bytes.fromhex(value))
            elif dtype == "string":
                responses.append(value.encode())
    return responses


def tcp_server(port, echo_mode, file_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', port))
    sock.listen(5)
    print(f"TCP server listening on port {port}")

    responses = parse_csv(file_path) if file_path else []

    try:
        while True:
            client_sock, client_addr = sock.accept()
            print(f"Connection from {client_addr}")

            try:
                if echo_mode:
                    while True:
                        data = client_sock.recv(4096)
                        if not data:
                            break
                        client_sock.sendall(data)
                else:
                    for response in responses:
                        data = client_sock.recv(4096)
                        if not data:
                            break
                        client_sock.sendall(response)
                    client_sock.shutdown(socket.SHUT_RDWR)
            except socket.error as e:
                print(f"Error: {e}")
            finally:
                print(f"Connection closed from {client_addr}")
                client_sock.close()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        sock.close()


def udp_server(port, echo_mode, file_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port))
    print(f"UDP server listening on port {port}")

    responses = parse_csv(file_path) if file_path else []

    try:
        while True:
            data, client_addr = sock.recvfrom(4096)
            print(f"Connection from {client_addr}")

            try:
                if echo_mode:
                    sock.sendto(data, client_addr)
                else:
                    for response in responses:
                        data, client_addr = sock.recvfrom(4096)
                        if not data:
                            break
                        sock.sendto(response, client_addr)
                    # UDP 서버는 연결 상태를 유지하지 않으므로, 연결 종료와 관련된 특별한 처리가 필요 없음
            except socket.error as e:
                print(f"Error: {e}")
            finally:
                print(f"Connection closed from {client_addr}")
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        sock.close()


def main():
    parser = argparse.ArgumentParser(description="Network Utility")

    subparsers = parser.add_subparsers(dest='mode', required=True)

    check_parser = subparsers.add_parser('check', help='Check if a TCP port is open')
    check_parser.add_argument('host', type=str, help='Host to check')
    check_parser.add_argument('port', type=int, help='Port to check')

    client_parser = subparsers.add_parser('client', help='Run as a TCP/UDP client')
    client_parser.add_argument('protocol', choices=['tcp', 'udp'], help='Protocol to use')
    client_parser.add_argument('host', type=str, help='Server host')
    client_parser.add_argument('port', type=int, help='Server port')
    client_parser.add_argument('-f', type=str, help='File to read data from')
    client_parser.add_argument('-u', action='store_true', help='Read data from user input')

    server_parser = subparsers.add_parser('server', help='Run as a TCP/UDP server')
    server_parser.add_argument('protocol', choices=['tcp', 'udp'], help='Protocol to use')
    server_parser.add_argument('port', type=int, help='Port to listen on')
    server_parser.add_argument('-e', action='store_true', help='Echo received data')
    server_parser.add_argument('-f', type=str, help='File to read responses from')

    args = parser.parse_args()

    if args.mode == 'check':
        if is_tcp_port_open(args.host, args.port):
            print(f"TCP port {args.port} on {args.host} is open.")
        else:
            print(f"TCP port {args.port} on {args.host} is closed.")
    elif args.mode == 'client':
        if args.protocol == 'tcp':
            tcp_client(args.host, args.port, args.f is not None, args.f)
        elif args.protocol == 'udp':
            udp_client(args.host, args.port, args.f is not None, args.f)
    elif args.mode == 'server':
        if args.protocol == 'tcp':
            tcp_server(args.port, args.e, args.f)
        elif args.protocol == 'udp':
            udp_server(args.port, args.e, args.f)


if __name__ == "__main__":
    main()
