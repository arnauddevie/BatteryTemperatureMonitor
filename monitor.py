import os
import re
import csv
import glob
import time
from temperature_sensor_class import *

def deblank(string:str):
    return string.lstrip().rstrip()

celsius= u'\N{DEGREE SIGN}' + 'C'

#sensor_base_address = '28-000007'
sensor_base_address = ''
sensorID_pattern = '[0-9A-Fa-f]{6}'
regexp = re.compile(sensorID_pattern)

sensor_list = list()
program_list = list()
cellID_list = list()
temperature_list = list()

with open('mapping.csv') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        if len(row) is 4:
            if regexp.search(row[0]) is not None:
                sensor_list.append(sensor_base_address + deblank(row[0]))
                program_list.append(deblank(row[1]))
                cellID_list.append(deblank(row[2]))
                temperature_list.append(int(row[3]))

print('Found {} valid rows in mapping.CSV'.format(len(sensor_list)))

program_dict = dict(zip(sensor_list, program_list))
cellID_dict = dict(zip(sensor_list, cellID_list))
temperature_dict = dict(zip(sensor_list, temperature_list))

# Turn ON GPIO and temperature sensors
# os.system('modprobe w1-gpio')
# os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
registered_devices = set()
cells = list()

while True:
    device_folder = glob.glob(base_dir + '28*')

    attached_devices = set()
    detached_devices = set(sensor_list)
    lost_devices = set()


    for device in device_folder:
        sensor_ID = device[-6:]
        if sensor_ID not in attached_devices:
            attached_devices.add(sensor_ID)
            detached_devices.discard(sensor_ID)
            print('Sensor ID {} attached @ {}'.format(sensor_ID, time.ctime()))

    lost_devices = registered_devices.difference(attached_devices)
    for sensor_ID in lost_devices:
        registered_devices.discard(sensor_ID)
        cells[:] = [cell for cell in cells if cell.sensorID is not sensor_ID]
        print('Sensor ID {} lost @ {}'.format(sensor_ID, time.ctime()))
    	
    for sensor_ID in attached_devices:
        if sensor_ID not in registered_devices:
            registered_devices.add(sensor_ID)
            print('Sensor ID {} registered @ {}'.format(sensor_ID, time.ctime()))
            cells.append(MonitoredCell(cellID_dict[sensor_ID], base_dir, sensor_ID, program_dict[sensor_ID], 'NCRB', '001', temperature_dict[sensor_ID], 30, 35, False))

    print(attached_devices)
    print('::::::::::::::')
    print(detached_devices)
    print('::::::::::::::')
    print(registered_devices)
    print('::::::::::::::')
    print(lost_devices)

    print('\nDetected the following {} sensors:\n'.format(len(cells)))
    for cell in cells:
        try:
            cell.update_Temperature()
            cell.check_Status()
            print(str.join(' :: ', (cell.cellID, cell.sensorID[-6:], cell.status, str(cell.currentTemperature) + celsius)))
            # print('Sensor ID: '+ cell.sensorID)
            # print('Cell ID: ' + cell.cellID)
            # print('Ambient temperature: ' + str(cell.ambientTemperature) + celsius)
            # print('Warning: ' + str(cell.warningThreshold) + celsius)
            # print('Alarm: ' + str(cell.alarmThreshold) + celsius)
            # print('These settings are valid') if cell.validSettings else print('These settings are incorrect')
            # print('Current temperature: ' + str(cell.currentTemperature) + celsius)
            # print('Average temperature: ' + str(cell.averageTemperature) + celsius)
            # print('Status: ' + cell.status)
            # print('\n')
        except NameError:
            print('Could not read from device ' + cell.sensorID + '\n')
        except FileNotFoundError:
            print('Could not locate file for device ' + cell.sensorID + '\n')
    # Update after a fixed period (in seconds)
    time.sleep(60)

