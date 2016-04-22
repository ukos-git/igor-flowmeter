#!/usr/bin/env python

import MySQLdb
from MySQLdb.constants import CLIENT
import os
import socket
import decimal
import struct
from time import sleep
from MKFlowMessage import FBconvertLong # converter for long numbers to float and percent
#cvd-client->rbBmSDP7fSKp87b5

class MKDatabase(object):
    ip = "132.187.77.71"
    sql = ""
    connected = False
    ready = False
    messageID = -1
    hostname = ""
    recording = False
    recordingID = -1
    fileName = ""
    storage_description = 50
    storage_values = 30

    def __init__(self):
        self.test()
        decimal.getcontext().prec = 2

    def open(self):
        if self.isOpen():
            return True
        try:
            dbHost = self.getIP()
            dbName = "cvd"
            dbUser = "cvd-client"
            dbPass = "rbBmSDP7fSKp87b5"
            self.db = MySQLdb.connect(
                host = dbHost,
                user = dbUser,
                passwd = dbPass,
                db = dbName,
                client_flag = CLIENT.FOUND_ROWS
                )
        except:
            print "database open failed."
            return False
        else:
            self.connected = True
            return True
    def close(self):
        try:
            # only close if network available and db was opened before
            if self.checkIP() and self.isOpen():
                self.db.close()
        except:
            print "database close failed."
        else:
            self.connected = False

    def isOpen(self):
        return self.connected

    def write(self, sql, update = False):
        # on update statements rise also if no lines were affected
        affectedRows = 0
        if not self.open():
            raise
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            affectedRows = cursor.rowcount
            cursor.close()
            self.db.commit()
        except:
            print "database write failed."
            print sql
            try:
                self.db.rollback()
                self.close()
            except:
                print "database rollback failed."
            raise
        else:
            if update and affectedRows == 0:
                raise
            return affectedRows

    def read(self, sql):
        affectedRows = 0
        if not self.open():
            return []
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            data = cursor.fetchone()
            affectedRows = cursor.rowcount
            cursor.close()
            self.close()
        except:
            print "database read failed."
            print sql
            cursor.close()
            self.close()
            data = []

        if affectedRows:
            return data
        else:
            return []

    def writeArduino(self, sql):
        try:
            self.write(sql, True)
            self.close()
        except:
            try:
                # create database and try again.
                self.createArduino()
                self.resetArduino()
                self.write(sql)
                self.close()
            except:
                return False
            else:
                return True
        else:
            return True

    def writeRecording(self, sql):
        try:
            self.write(sql, True)
            self.close()
        except:
            try:
                self.createRecording()
                self.resetRecording()
                self.write(sql)
                self.close()
            except:
                return False
            else:
                return True
        else:
            return True

    def writeFlowbus(self, sql):
        try:
            self.write(sql)
            self.close()
        except:
            try:
                self.createFlowbus()
                self.write(sql)
                self.close()
            except:
                return False
            else:
                return True
        else:
            return True

    def writeMessage(self, sql):
        try:
            self.write(sql, True)
            self.close()
        except:
            try:
                self.createMessage()
                self.resetMessage()
                self.write(sql)
                self.close()
            except:
                return False
            else:
                return True
        else:
            return True

    def test(self):
        self.open()
        sql="SELECT VERSION()"
        data = self.read(sql)
        self.close()
        print "MySQL version : %s " % data

    def getHostname(self):
        return socket.gethostname()

    def isRaspberry(self):
        if self.hostname == "":
            self.hostname = getHostname()
        if (self.hostname == "raspberrypi"):
            return True
        else:
            return False

    def getIP(self):
        if (self.hostname == "lab117"):
            self.ip = 'localhost'
        else:
            self.ip == "132.187.77.71"
        while not self.checkIP():
            print "ip not found"
            sleep(0.5)
        return self.ip

    def checkIP(self):
        if os.system("ping -c 1 -W 1 " + self.ip + " > /dev/null") == 0:
            return True
        else:
            return False

    def createArduino(self):
        sql = """CREATE TABLE IF NOT EXISTS `runtime_arduino` (
                `temperature` decimal(6,2) NOT NULL DEFAULT '0',
                `pressure` decimal(6,2) NOT NULL DEFAULT '0',
                `argon` decimal(6,2) NOT NULL DEFAULT '0',
                `ethanol` decimal(6,2) NOT NULL DEFAULT '0',
                `spTemperature` int(11) NOT NULL DEFAULT '0',
                `spPressure` int(11) NOT NULL DEFAULT '1000',
                `spEthanol` int(11) NOT NULL DEFAULT '0',
                `spArgon` int(11) NOT NULL DEFAULT '0'
                ) ENGINE=MEMORY DEFAULT Charset=utf8;"""
        self.write(sql)

    def resetArduino(self):
        sql = """INSERT INTO `runtime_arduino`
                        (`temperature`, `pressure`, `argon`, `ethanol`, `spTemperature`, `spPressure`, `spEthanol`, `spArgon`)
                    VALUES
                        (0, 0, 0, 0, 0, 0, 0, 0);"""
        self.write(sql)

    def createFlowbus(self):
        sql = """
        CREATE TABLE IF NOT EXISTS `runtime_flowbus`
        (
            `instrument`    smallint(2) NOT NULL DEFAULT '0',
            `process`       smallint(2) NOT NULL,
            `flowBus`       smallint(2) NOT NULL,
            `dataType`      tinyint(1) NOT NULL DEFAULT '0',
            `parameter`     binary(%i) NOT NULL DEFAULT '0',
            `data`          binary(%i) NOT NULL DEFAULT '0',
            `time`          decimal(7,2) NOT NULL DEFAULT '0',
            UNIQUE KEY `instrument` (`instrument`,`process`,`flowBus`)
        )
        ENGINE=MEMORY
        DEFAULT CHARSET=utf8;""" % (self.storage_description, self.storage_values)
        self.write(sql)

    def createRecording(self):
        sql = """CREATE TABLE IF NOT EXISTS `runtime_recording` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `recording` tinyint(4) NOT NULL DEFAULT '0',
                `id_recording` int(11) DEFAULT '0',

                PRIMARY KEY (`id`)
                ) ENGINE=MEMORY DEFAULT Charset=utf8 AUTO_INCREMENT=40;"""
        self.write(sql)

        sql = """CREATE TABLE IF NOT EXISTS `recording` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `recording` tinyint(4) NOT NULL DEFAULT '0',
                `filename` text NOT NULL,
                PRIMARY KEY (`id`)
                ) ENGINE=InnoDB DEFAULT Charset=utf8 AUTO_INCREMENT=40;"""
        self.write(sql)

    def resetRecording(self):
        sql = """INSERT INTO `runtime_recording`
                        (`recording`)
                    VALUES
                        (0)"""
        self.write(sql)

    def createMessage(self):
        sql = """CREATE TABLE IF NOT EXISTS `cvd`.`runtime_message` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `ready` tinyint(4) NOT NULL DEFAULT '0',
                `id_message` int(11) DEFAULT '0',

                PRIMARY KEY (`id`)
                ) ENGINE=MEMORY DEFAULT Charset=utf8 AUTO_INCREMENT=40;"""
        self.write(sql)

        sql = """CREATE TABLE IF NOT EXISTS  `cvd`.`message` (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `processed` tinyint(4) NOT NULL DEFAULT '0',
                `text` text NOT NULL,
                PRIMARY KEY (`id`)
                ) ENGINE=InnoDB DEFAULT Charset=utf8 AUTO_INCREMENT=40;"""
        self.write(sql)

    def resetMessage(self):
        sql = """INSERT INTO `cvd`.`runtime_message`
                        (`ready`)
                    VALUES
                        (0)"""
        self.write(sql)
        sql = """DELETE FROM `cvd`.`message`
                    WHERE `processed` = 1"""
        self.write(sql)

    def setSetpoint(self, temperature, pressure, argon, ethanol):
        sql = """UPDATE `cvd`.`runtime_arduino`
                    SET	`spTemperature` = %s,
                            `spPressure`	= %s,
                            `spEthanol`	= %s,
                            `spArgon`	= %s
                    LIMIT 1;"""  % (temperature, pressure, ethanol, argon)
        return self.writeArduino(sql)

    def setData(self, temperature, pressure, argon, ethanol):
        try:
            self.temperature = decimal.Decimal(temperature)
            self.pressure = decimal.Decimal(pressure)
            self.argon = decimal.Decimal(argon)
            self.ethanol = decimal.Decimal(ethanol)
        except:
            self.temperature = 0.00
            self.pressure = 0.00
            self.argon = 0.00
            self.ethanol = 0.00
        sql = """UPDATE `cvd`.`runtime_arduino`
                SET	`temperature`	= %s,
                        `pressure`	= %s,
                        `ethanol`	= %s,
                        `argon`		= %s
                LIMIT 1;"""  % (self.temperature, self.pressure, self.ethanol, self.argon)
        return self.writeArduino(sql)

    def setLogFile(self, fileName):
        id = self.getRecordingID()
        if id < 0:
            return False
        sql = """UPDATE `cvd`.`recording`
                    SET	`filename`  = '%s',
                        `recording` = 1
                    WHERE `id` = %i
                    LIMIT 1;""" % (fileName, id)
        if not self.writeRecording(sql):
            return False
        if self.getLogFile() == fileName:
            return True
        else:
            return False

    def isRecording(self):
        sql = """SELECT `recording`
                    FROM `cvd`.`runtime_recording`
                    LIMIT 1;"""
        try:
            data = self.read(sql)
        except:
            return False
        if not len(data) == 1:
            return False
        else:
            if data[0]:
                return True
            else:
                return False

    def stopRecording(self):
        sql = """UPDATE `cvd`.`runtime_recording`
                SET	`recording` = 0;"""
        if not self.writeRecording(sql):
            return False
        sql = """UPDATE `cvd`.`recording`
                SET	`recording` = 0
                WHERE `recording` = 1;"""
        if not self.writeRecording(sql):
            return False
        self.recordingID = -1
        return True

    def startRecording(self, filename = ''):
        self.stopRecording

        sql = """INSERT INTO `cvd`.`recording` (
                `id` ,`time` , `recording` , `filename` )
                VALUES (
                NULL , CURRENT_TIMESTAMP , 1, '%s')""" % filename
        if not self.writeRecording(sql):
            return False
        sql = """SELECT `id`
        FROM `cvd`.`recording`
                WHERE `recording` = 1
                LIMIT 1;"""
        data = self.read(sql)
        if not len(data) == 1:
            return False
        sql = """UPDATE `cvd`.`runtime_recording`
                SET `id_recording` = %i,
                    `recording` = 1
                LIMIT 1;""" % data
        if not self.writeRecording(sql):
            return False
        return True

    def getRecordingID(self):
        sql = """SELECT `id_recording`
                    FROM `cvd`.`runtime_recording`
                    LIMIT 1;"""
        data = self.read(sql)
        if (len(data) == 1):
            return int(data[0])
        else:
            return -1

    def getLogFile(self):
        if not self.isRecording():
            return ""
        # get id from memory table
        recordingID = self.getRecordingID()
        # update filename from disc table if not already saved in class
        if not (recordingID == self.recordingID) or len(self.fileName) == 0:
            sql = """SELECT `filename`
                    FROM `cvd`.`recording`
                    WHERE `id` = %i;""" % recordingID
            data = self.read(sql)
            if len(data) == 1:
                self.fileName = data[0]
            else:
                self.fileName = ''
            self.recordingID = recordingID
        return self.fileName

    def setMessage(self, message):
        sql = """INSERT INTO `cvd`.`message`
                (`text`) VALUES ('%s');"""  % (message)
        if self.writeMessage(sql):
            return self.updateMessage()
        return False

    def updateMessage(self):
        sql = """SELECT `id` FROM `cvd`.`message`
                WHERE `processed` = 0
                LIMIT 1;"""
        data = self.read(sql)
        if (len(data) == 1):
            id_message = data[0]
            ready = 1
        else:
            ready = 0
            id_message = -1

        sql = """UPDATE `cvd`.`runtime_message`
                SET `ready` = %i,
                    `id_message` = %i
                LIMIT 1;""" % (ready, id_message)
        return self.writeMessage(sql)

    def isReady(self):
        if self.ready:
            return True
        sql = """SELECT `ready`, `id_message`
                FROM `cvd`.`runtime_message`;"""
        try:
            data = self.read(sql)
        except:
            return False
        if not len(data) == 2:
                data = (0,-1)
        (self.ready, self.messageID) = data
        if self.ready:
            return True
        else:
            return False

    def getMessage(self):
        self.message = ""
        # read from runtime (memory table)
        if self.isReady():
            # ready flag did also read out messageID.
            # get message string from cvd.message
            sql = """SELECT `text`
                FROM `cvd`.`message`
                WHERE `id` = %i
                LIMIT 1;""" % self.messageID
            data = self.read(sql)
            if (len(data) == 1):
                self.message = data[0]
                # mark message in cvd.message as processed 
                sql = """UPDATE `cvd`.`message`
                    SET `processed` = 1
                    WHERE `id` = %i;""" % self.messageID
                self.writeMessage(sql)
            self.updateMessage()
        # reset readout
        self.ready = False
        return self.message

    def setFlowbus(self, instrument, process, flowBus, dataTypeString, dataInput, timeInput, parameterName):
        time = decimal.Decimal(timeInput)
        parameterName = parameterName.encode("hex")
        if (dataTypeString == "character"):
            dataType = 0
            data = format(int(dataInput), 'x')
        elif(dataTypeString == "integer"):
            dataType = 1
            data = format(int(dataInput), 'x')
        elif(dataTypeString == "long"):
            dataType = 2
            data = format(int(dataInput), 'x')
        elif(dataTypeString == "string"):
            dataType = 3
            data = dataInput.encode("hex")
        else:
            raise ValueError("can not identify dataType at setFlowBus()")

        sql = """
        INSERT INTO `cvd`.`runtime_flowbus`
        (`instrument`,`process`,`flowBus`,`dataType`,`data`,`time`, `parameter`)
        VALUES
        (%i, %i, %i, %i, UNHEX(LPAD('%s',%i,'0')), %.2f, UNHEX(LPAD('%s',%i,'0')))""" % (instrument, process, flowBus, dataType, data, self.storage_values * 2, time, parameterName, self.storage_description * 2)
        sql += """
        ON DUPLICATE KEY UPDATE
        `data` = UNHEX(LPAD('%s',%i,'0')),
        `time` = %.2f;""" % (data, self.storage_values * 2, time)
        self.writeFlowbus(sql)

    def getFlowbus(self, instrument, process, flowBus):
        sql = """
        SELECT `dataType`,TRIM(LEADING '0' FROM HEX(`data`)),`time`,TRIM(LEADING '0' FROM HEX(`parameter`))
        FROM `cvd`.`runtime_flowbus`
        WHERE
        (   `instrument`    = %i
        AND `process`       = %i
        AND `flowBus`       = %i);
        """ % (instrument, process, flowBus)
        data = self.read(sql)
        if (len(data) == 4):
            (dataType, dataOut, timeOut, parameter) = data
        else:
            return (-1,-1,-1)

        parameter = parameter.decode("hex")
        time = decimal.Decimal(timeOut)
        if (dataType == 0):
            data = int(dataOut, 16)
        elif(dataType == 1):
            data = int(dataOut, 16)
        elif(dataType == 2):
            data = FBconvertLong(process, flowBus, int(dataOut,16))
        elif(dataType == 3):
            data = dataOut.decode("hex")
        else:
            raise ValueError("can not identify dataType at getFlowBus()")

        return (parameter, data, time)

    def getAll(self):
        self.open()
        sql = """SELECT temperature, pressure, ethanol, argon,
                             spTemperature, spPressure, spEthanol, spArgon
                      FROM `cvd`.`runtime_arduino`
                      LIMIT 1"""
        data = self.read(sql)
        if len(data) == 0:
            print "database readout failed for arduino!"
            data = (-1,-1,-1,-1, -1,-1,-1,-1)
        (self.temperature, self.pressure, self.ethanol, self.argon, self.spTemperature, self.spPressure, self.spEthanol, self.spArgon) = data

