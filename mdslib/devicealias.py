import logging

import time

from .connection_manager.errors import CLIError, CustomException
from .constants import ENHANCED, BASIC

log = logging.getLogger(__name__)


class InvalidMode(CustomException):
    pass


class DeviceAlias(object):
    """
    Device Alias module

    :param switch: switch object on which device-alias operations needs to be executed
    :type switch: Switch

    :example:
        >>> da = DeviceAlias(switch = switch_obj)

    """

    def __init__(self, sw):
        self.__swobj = sw

    @property
    def mode(self):
        """
        set device-alias mode or
        get device-alias mode

        :getter:
        :return: mode
        :rtype: str
        :values: ['basic', 'enhanced']
        :example:
            >>>
            >>> da = DeviceAlias(switch = switch_obj)
            >>> print(da.mode)
            enhanced
            >>>

        :setter:
        :param mode: mode
        :type mode: str
        :values: ['basic', 'enhanced']
        :raises InvalidMode: if mode is not to either 'basic' or 'enhanced'
        :raises CLIError: If there is any cli error
        :example:
            >>>
            >>> da = DeviceAlias(switch = switch_obj)
            >>> da.mode = 'basic'
            >>>

        """

        facts_out = self.__get_facts()
        return self.__get_mode(facts_out)

    @mode.setter
    def mode(self, mode):
        log.debug("Setting device alias mode to " + mode)
        if mode.lower() == ENHANCED:
            cmd = "device-alias database ; device-alias mode enhanced"
        elif mode.lower() == BASIC:
            cmd = "device-alias database ; no device-alias mode enhanced"
        else:
            raise InvalidMode("Invalid device alias mode: " + str(
                mode) + ". Valid values are " + ENHANCED + "," + BASIC)
        out = self.__swobj.config(cmd)
        if out is not None:
            msg = out['msg']
            dist = self.distribute
            if dist and dist is not None:
                self.__send_commit(mode)
            raise CLIError(cmd, msg)
        dist = self.distribute
        if dist and dist is not None:
            self.__send_commit(mode)

    @property
    def distribute(self):
        """
        set device-alias distribute configuration or
        get device-alias distribute configuration

        :getter:
        :return: distribute
        :rtype: bool
        :example:
            >>>
            >>> da = DeviceAlias(switch = switch_obj)
            >>> print(da.distribute)
            True
            >>>

        :setter:
        :param distribute: set to True if distribute needs to be enabled or set to False if distribute needs to be disabled
        :type distribute: bool
        :raises CLIError: If there is any cli command error
        :raises TypeError: If the passed value is not of type bool

        :example:
            >>>
            >>> da = DeviceAlias(switch = switch_obj)
            >>> da.distribute = True
            >>>

        """

        facts_out = self.__get_facts()
        dis = self.__get_distribute(facts_out)
        if dis.lower() == 'enabled':
            return True
        else:
            return False

    @distribute.setter
    def distribute(self, distribute):
        if type(distribute) is not bool:
            raise TypeError("Only bool value(true/false) supported.")
        if distribute:
            cmd = "device-alias database ; device-alias distribute"
            log.debug("Setting device alias mode to 'Enabled'")
            log.debug(cmd)
        else:
            cmd = "device-alias database ; no device-alias distribute"
            log.debug("Setting device alias mode to 'Disabled'")
            log.debug(cmd)
        out = self.__swobj.config(cmd)
        if out is not None:
            msg = out['msg']
            raise CLIError(cmd, msg)

    @property
    def locked(self):
        """
        Check if device-alias has acquired lock or not

        :return: locked: Returns True if device-alias lock is acquired else returns False
        :rtype: bool
        """

        facts_out = self.__get_facts()
        if self.__locked_user(facts_out) is None:
            return False
        return True

    @property
    def database(self):
        """
        Returns device-alias database in dict(name:pwwn) format, if there are no device-alias entries then it returns None

        :return: database or None
        :rtype: dict(name:pwwn)
        """

        retout = {}
        facts_out = self.__get_facts()
        allentries = facts_out.get('device_alias_entries', None)
        if allentries is None:
            # Means there are no entries
            return None
        else:
            if type(allentries) is dict:
                # That means there is only one entry in the database
                # hence we need to convert allentries to a list, if there are more than
                # one entry in the database then allentries will not be a dict it will be a list
                allentries = [allentries]
            for eachentry in allentries:
                retout[eachentry['dev_alias_name']] = eachentry['pwwn']
            return retout

    def create(self, namepwwn):
        """
        Create device alias entries

        :param namepwwn: name and pwwwn
        :type namepwwn: dict (name: pwwn)
        :return: None
        :raises CLIError: If there is any cli command error

        :example:
            >>>
            >>> da = DeviceAlias(switch = switch_obj)
            >>> da.create({'device1': '21:00:00:0e:1e:30:34:a5','device2': '21:00:00:0e:1e:30:3c:c5'})
            >>>
         """

        mode = self.mode
        for name, pwwn in namepwwn.items():
            log.debug("Creating device alias with name:pwwn  " + name + " : " + pwwn)
            cmd = "device-alias database ; "
            cmd = cmd + " device-alias name " + name + " pwwn " + pwwn + " ; "
            out = self.__swobj.config(cmd)
            if out is not None:
                msg = out['msg']
                self.__clear_lock_if_enhanced(mode)
                dist = self.distribute
                if dist and dist is not None:
                    self.__send_commit(mode)
                if "Device Alias already present" in msg:
                    log.info("The command : " + cmd + " was not executed because Device Alias already present")
                elif "Another device-alias already present with the same pwwn" in msg:
                    log.info("The command : " + cmd + " was not executed because Device Alias already present")
                else:
                    raise CLIError(cmd, msg)
        dist = self.distribute
        if dist and dist is not None:
            self.__send_commit(mode)

    def delete(self, name):
        """
        Delete device alias entry

        :param name: name of device alias that needs to be deleted
        :type name: str
        :return: None
        :raises CLIError: If there is any cli command error

        :example:
            >>>
            >>> da = DeviceAlias(switch = switch_obj)
            >>> da.delete('device1')

        """

        mode = self.mode
        log.debug("Deleting device alias with args " + name)
        cmd = "device-alias database ; no device-alias name " + name
        out = self.__swobj.config(cmd)
        if out is not None:
            msg = out['msg']
            self.__clear_lock_if_enhanced(mode)
            dist = self.distribute
            if dist and dist is not None:
                self.__send_commit(mode)
            raise CLIError(cmd, msg)
        dist = self.distribute
        if dist and dist is not None:
            self.__send_commit(mode)

    def rename(self, oldname, newname):
        """
        Rename device alias entry

        :param oldname: old device alias name
        :type oldname: str
        :param newname: new device alias name
        :type newname: str
        :return: None
        :raises CLIError: If there is any cli command error

        :example:
            >>>
            >>> da = DeviceAlias(switch = switch_obj)
            >>> da.rename('device1','device_new')
            >>>

        """

        mode = self.mode
        log.debug("Renaming device alias with args " + oldname + " " + newname)
        cmd = "device-alias database ; device-alias rename " + oldname + " " + newname
        out = self.__swobj.config(cmd)
        if out is not None:
            msg = out['msg']
            self.__clear_lock_if_enhanced(mode)
            dist = self.distribute
            if dist and dist is not None:
                self.__send_commit(mode)
            raise CLIError(cmd, msg)

        dist = self.distribute
        if dist and dist is not None:
            self.__send_commit(mode)

    def clear_lock(self):
        """
        Clears lock if lock is acquired

        :param: None
        :return: None

        :example:
            >>>
            >>> da = DeviceAlias(switch = switch_obj)
            >>> da.clear_lock()
            >>>

        """

        log.debug("Sending the cmd clear device-alias session")
        cmd = "terminal dont-ask ; device-alias database ; clear device-alias session ; no terminal dont-ask "
        self.__swobj.config(cmd)

    def clear_database(self):
        """
        Clears database entries

        :param: None
        :return: None
        :raises CLIError: If there is any cli command error

        :example:
            >>>
            >>> da = DeviceAlias(switch = switch_obj)
            >>> da.clear_database()
            >>>

        """

        mode = self.mode
        log.debug("Sending the cmd clear device-alias database")
        cmd = "terminal dont-ask ; device-alias database ; clear device-alias database ; no terminal dont-ask "
        out = self.__swobj.config(cmd)
        if out is not None:
            msg = out['msg']
            self.__clear_lock_if_enhanced(mode)
            dist = self.distribute
            if dist and dist is not None:
                self.__send_commit(mode)
            raise CLIError(cmd, msg)

        dist = self.distribute
        if dist and dist is not None:
            self.__send_commit(mode)

    def __get_facts(self):
        log.debug("Getting device alias facts")
        retoutput = {}
        out = self.__swobj.show("show device-alias database")
        if out:
            num = out['number_of_entries']
            da = out['TABLE_device_alias_database']['ROW_device_alias_database']

            retoutput['number_of_entries'] = num
            retoutput['device_alias_entries'] = da
        shdastatus = self.__swobj.show("show device-alias status")

        return dict(retoutput, **shdastatus)

    @staticmethod
    def __get_mode(facts_out):
        return facts_out['database_mode']

    @staticmethod
    def __get_distribute(facts_out):
        return facts_out['fabric_distribution']

    @staticmethod
    def __locked_user(facts_out):
        if 'Locked_by_user' in facts_out.keys():
            log.debug(facts_out['Locked_by_user'])
            return facts_out['Locked_by_user']
        else:
            return None

    def __send_device_alias_cmds(self, command, facts_out=None, mode=None, skipcommit=False):
        if facts_out is None:
            facts_out = self.__get_facts()
        if mode is None:
            mode = self.mode

        if 'distribute' in command:
            dist = None
        else:
            dist = self.distribute
        log.debug("mode is " + mode)
        log.debug("distribute is " + str(dist))
        lock_user = self.__locked_user(facts_out)
        if lock_user is not None:
            log.error("Switch has acquired cfs device-alias lock by user " + lock_user)
            self.__clear_lock_if_enhanced(mode)
            raise CLIError(command, "Switch has acquired cfs device-alias lock by user " + lock_user)

        log.debug("Sending the command..")
        log.debug(command)
        out = self.__swobj.config(command)
        if out is not None:
            msg = out['msg']
            if "Device Alias already present" in msg:
                log.info("The command : " + command + " was not executed because Device Alias already present")
            elif "Another device-alias already present with the same pwwn" in msg:
                log.info("The command : " + command + " was not executed because Device Alias already present")
            else:
                log.error(msg)
                self.__clear_lock_if_enhanced(mode)
                raise CLIError(command, msg)
            # self._clear_lock_if_enhanced(mode)

        if skipcommit:
            return False, None
        else:
            if dist and dist is not None:
                self.__send_commit(mode)

    def __send_commit(self, mode):
        cmd = "terminal dont-ask ; device-alias commit ; no terminal dont-ask "
        log.debug(cmd)
        out = self.__swobj.config(cmd)
        log.debug(out)
        if out is not None:
            msg = out['msg'].strip("\n").strip()
            if "There are no pending changes" in msg:
                log.debug("The commit command was not executed because Device Alias already present")
            elif "Device-alias enhanced zone member present" in msg:
                # log.error(msg)
                self.__clear_lock_if_enhanced(mode)
                raise CLIError(cmd, msg)
            elif "Commit in progress. Check the status." in msg:
                log.debug("Commit in progress...sleep for 5 sec")
                time.sleep(5)
            else:
                raise CLIError(cmd, msg)

    def __clear_lock_if_enhanced(self, mode):
        if mode.lower() == ENHANCED:
            self.clear_lock()
