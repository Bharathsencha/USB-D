#!/usr/bin/env python3
import os
import subprocess
import re
import time

def get_usb_devices():
    """Find USB devices using multiple methods"""
    usb_devices = []
    
    try:
        # Method 1: Use lsblk to find removable devices
        result = subprocess.run(['lsblk', '-d', '-o', 'NAME,RO,RM,SIZE,TYPE'], 
                              capture_output=True, text=True, check=True)
        
        for line in result.stdout.splitlines()[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 5 and parts[4] == 'disk' and parts[2] == '1':  # RM=1 means removable
                device_name = '/dev/' + parts[0]
                # Only add the device, not partitions
                if not any(char.isdigit() for char in parts[0]):
                    usb_devices.append(device_name)
                
        # Method 2: Check /dev/disk/by-path for USB devices
        by_path = '/dev/disk/by-path'
        if os.path.exists(by_path):
            for item in os.listdir(by_path):
                if 'usb' in item.lower():
                    full_path = os.path.realpath(os.path.join(by_path, item))
                    # Only add if it's a device (not partition) and not already in the list
                    if full_path not in usb_devices and not any(char.isdigit() for char in full_path):
                        usb_devices.append(full_path)
                        
    except Exception as e:
        print(f"Error finding USB devices: {e}")
        
    return usb_devices

def unmount_device(device):
    """Unmount all partitions of a device"""
    try:
        # Find all partitions of this device
        partitions = []
        for part in os.listdir('/dev'):
            if part.startswith(device.split('/')[-1]) and part != device.split('/')[-1]:
                partitions.append('/dev/' + part)
        
        # Unmount all partitions
        for partition in partitions:
            try:
                print(f"Unmounting {partition}...")
                subprocess.run(['umount', '-f', partition], check=True, timeout=10)
            except subprocess.TimeoutExpired:
                print(f"Force unmounting {partition}...")
                subprocess.run(['umount', '-l', partition], check=True)
            except Exception as e:
                print(f"Could not unmount {partition}: {e}")
        
        # Wait a moment for unmount to complete
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Error unmounting device {device}: {e}")
        return False

def wipe_device(device):
    """Completely wipe a USB device"""
    try:
        print(f"Wiping {device}...")
        
        # Unmount all partitions first
        if not unmount_device(device):
            print(f"Failed to unmount {device}, trying to continue...")
        
        # Use dd to zero out the first part of the disk (this destroys partition table)
        print("Zeroing out partition table...")
        subprocess.run(['dd', 'if=/dev/zero', f'of={device}', 'bs=1M', 'count=10'], 
                      check=True, timeout=30)
        
        # Wait a moment
        time.sleep(1)
        
        # Create a new partition table (MBR)
        print("Creating new partition table...")
        subprocess.run(['parted', '-s', device, 'mklabel', 'msdos'], check=True, timeout=10)
        
        # Create a new primary partition using the whole disk
        print("Creating new partition...")
        subprocess.run(['parted', '-s', device, 'mkpart', 'primary', 'fat32', '0%', '100%'], 
                      check=True, timeout=10)
        
        # Wait for partition to be recognized
        time.sleep(2)
        
        # Find the partition name
        partition = None
        for part in os.listdir('/dev'):
            if part.startswith(device.split('/')[-1]) and part != device.split('/')[-1]:
                partition = '/dev/' + part
                break
        
        if not partition:
            print(f"Could not find partition for {device}")
            return False
        
        # Format the partition
        print(f"Formatting {partition}...")
        subprocess.run(['mkfs.vfat', '-F', '32', '-n', 'USBDRIVE', partition], 
                      check=True, timeout=30)
        
        print(f"Successfully wiped and formatted {device}")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"Timeout while processing {device}")
        return False
    except Exception as e:
        print(f"Error wiping {device}: {e}")
        return False

def main():
    print("Finding USB devices...")
    devices = get_usb_devices()
    
    if not devices:
        print("No USB devices found")
        return
        
    print(f"Found USB devices: {devices}")
    
    for device in devices:
        # Double confirmation for each device
        confirm = input(f"Type 'YES' to wipe {device} (THIS WILL DESTROY ALL DATA): ")
        if confirm == 'YES':
            success = wipe_device(device)
            if success:
                print(f"Successfully processed {device}")
            else:
                print(f"Failed to process {device}")
        else:
            print(f"Skipping {device}")

if __name__ == '__main__':
    main()