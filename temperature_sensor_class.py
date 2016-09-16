import typecheck as tc

class MonitoredCell(object):
    """A battery cell with a DS18B20 temperature sensor for monitoring.

    Attributes:
        cellID: The full nickname of the cell in the Pakali system, as a string.
        sensorPath: The full path pointing to the folder where sensors' data are stored, as a string.
        sensorID: The 14-digit unique ID of the temperature sensor, as a string.
        make: The make of the cell, as a string.
        model: The model of the cell, as a string.
        number: The number of the cell in the Pakali system, as a string.
        ambientTemperature: The ambient temperature of the climate chamber, as an integer.
        warningThreshold: The warning level temperature, as an integer.
        alarmThreshold: The alarm level temperature, as an integer.
        enableLogging: Enable or disable logging of measured values to logfile, as a boolean.
        currentTemperature: The current temperature reported by the sensor, as a float.
        averageTemperature: The moving average of the measured temperature over the past (10) readings, as a float.
        recentReadings: The past (10) readings, as a list of floats.
        absoluteMaximumTemperature: The critical level temperature for all instances (non-editable)
        validSettings: editable settings will be checked at initialization to make sure they are valid (non-editable)
        status: current status('Normal'|'Warning'|'Alarm'), as a string.
    """
    @tc.typecheck
    def __init__(self, cellID:str, sensorPath:str, sensorID:str, make:str, model:str, number:str, ambientTemperature:int, warningThreshold:int, alarmThreshold:int, enableLogging:bool):
        """Return a new MonitoredCell object."""

        # Static setting common to all instances of this class (high level fail-safe)
        absoluteMaximumTemperature = 80

        # Editable
        self.cellID = cellID
        self.sensorPath = sensorPath
        self.sensorID = '28-000007' + sensorID
        self.make = make
        self.model = model
        self.number = number
        self.ambientTemperature = ambientTemperature
        self.warningThreshold = warningThreshold
        self.alarmThreshold = alarmThreshold
        self.enableLogging = enableLogging

        # Read only
        self.currentTemperature = 0.0
        self.averageTemperature = 0.0
        self.recentReadings = [0.0]*10
        self.absoluteMaximumTemperature = absoluteMaximumTemperature

        # Checking values of Attributes (typechecking is done by typecheck-decorator module at runtime)
        # Empty strings are "False"
        # Integer must be in correct range
        if  (
            cellID is not '' and
            make is not '' and
            model is not '' and
            number is not '' and
            ambientTemperature in range (-100, absoluteMaximumTemperature) and
            warningThreshold in range(ambientTemperature, alarmThreshold) and
            alarmThreshold in range(ambientTemperature, absoluteMaximumTemperature)
            ):
            self.validSettings = True
        else:
            self.validSettings = False

    # Placeholder methods

    def read_temp_raw(self,device_file):
        with open(device_file, 'r') as f:
            lines = f.readlines()
        return lines

    def read_temp(self):
        import os
        import time
        lines = self.read_temp_raw(os.path.join(self.sensorPath, self.sensorID, 'w1_slave'))
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            # temp_f = temp_c * 9.0 / 5.0 + 32.0
            # return temp_f
            return temp_c

    def sendSMS(self):
        from twilio.rest import TwilioRestClient

        # Your Account Sid and Auth Token from twilio.com/user/account
        account_sid = "AC3d1d94b03a9c324312b82ed931cde90e"
        auth_token  = "1b4c8b535453b43a35ea686a7aa60576"
        client = TwilioRestClient(account_sid, auth_token)

        message = client.messages.create(body = str.join(' :: ', (self.cellID, self.sensorID[-6:], self.status, str(self.currentTemperature), str(self.averageTemperature))),
            to="+18083877670",    # Replace with your phone number
            from_="+18082010840") # Replace with your Twilio number
        print(message.sid)


    def get_warningThreshold(self):
        """Return the warning level temperature as an integer."""
        return self.warningThreshold

    def get_alarmThreshold(self):
        """Return the alarm level temperature as an integer."""
        return self.alarmThreshold

    def update_Temperature(self):
        """Update the current temperature in Celsius as an float."""
        # Read current value from sensor
        self.currentTemperature = self.read_temp()
        # Drop the oldest data point
        self.recentReadings.pop()
        # Insert the new data point at the beginning of the list
        self.recentReadings.insert(0, self.currentTemperature)
        # Compute a new average temperature
        self.averageTemperature = sum(reading for reading in self.recentReadings) / len(self.recentReadings)

        return self.currentTemperature, self.averageTemperature

    def check_Status(self):
        """Checks and reports the current temperature against the warning and alarm level temperature, as a string."""

        if self.currentTemperature > self.alarmThreshold:
            self.status = 'Alarm'
        elif self.currentTemperature > self.warningThreshold:
            self.status = 'Warning'
        else:
            self.status = 'Normal'

        # self.sendSMS()

        return self.status

