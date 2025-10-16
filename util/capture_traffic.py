#!/usr/bin/env python3
# Script to capture network traffic from a Docker container and save as PCAP

import argparse
import subprocess
import os
import signal
import sys
import time


def get_container_pid(container_id):
    """Get the PID of the specified Docker container."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Pid}}", container_id],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting container PID: {e}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)


def start_capture(container_pid, output_file, interface=None):
    """Start capturing network traffic using tcpdump."""
    cmd = ["tcpdump", "-i", interface or f"any", "-w", output_file]
    
    # Use network namespace of the container
    if container_pid != "0":
        cmd = ["nsenter", "-t", container_pid, "-n"] + cmd
    
    print(f"Starting capture with command: {' '.join(cmd)}")
    return subprocess.Popen(cmd)


def main():
    parser = argparse.ArgumentParser(description="Capture network traffic from a Docker container")
    parser.add_argument("container_id", help="Docker container ID or name")
    parser.add_argument("-o", "--output", default="capture.pcap", help="Output PCAP file (default: capture.pcap)")
    parser.add_argument("-i", "--interface", help="Network interface to capture (default: any)")
    parser.add_argument("-t", "--time", type=int, help="Duration of capture in seconds")
    args = parser.parse_args()

    # Check if tcpdump is installed
    try:
        subprocess.run(["which", "tcpdump"], check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("Error: tcpdump is not installed. Please install it first.")
        print("On Ubuntu/Debian: sudo apt-get install -y tcpdump")
        print("On CentOS/RHEL: sudo yum install -y tcpdump")
        sys.exit(1)

    # Check if running as root
    if os.geteuid() != 0:
        print("This script must be run as root to capture network traffic.")
        print("Please run with sudo or as root user.")
        sys.exit(1)

    # Get container PID
    container_pid = get_container_pid(args.container_id)
    
    if container_pid == "0":
        print("Warning: Container PID is 0, which may indicate the container is not running.")
        proceed = input("Do you want to proceed capturing host traffic? (y/n): ")
        if proceed.lower() != 'y':
            sys.exit(0)
    
    print(f"Container PID: {container_pid}")
    
    # Start capture
    tcpdump_process = start_capture(container_pid, args.output, args.interface)
    
    try:
        print(f"Capturing traffic... Output will be saved to {args.output}")
        print("Press Ctrl+C to stop capturing.")
        
        if args.time:
            print(f"Capturing for {args.time} seconds...")
            time.sleep(args.time)
            tcpdump_process.terminate()
        else:
            # Wait until user interrupts
            tcpdump_process.wait()
    
    except KeyboardInterrupt:
        print("\nStopping capture...")
    finally:
        try:
            tcpdump_process.terminate()
            tcpdump_process.wait(timeout=5)
        except:
            # Force kill if termination doesn't work
            try:
                tcpdump_process.kill()
            except:
                pass
        
        print(f"Capture complete. Output saved to {args.output}")


if __name__ == "__main__":
    main()