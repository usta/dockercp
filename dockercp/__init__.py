# -*- coding: utf-8 -*-

import os
import tarfile
from importlib.util import find_spec
from abc import ABCMeta, abstractmethod
from tempfile import mkstemp

__version__ = "0.0"


class IFetcher(metaclass=ABCMeta):
    def __init__(self, src_container, src_path, dest_path, buffer_len):
        self.srcContainer = src_container
        self.srcPath = src_path
        self.destPath = dest_path
        self.bufferLen = buffer_len

    @abstractmethod
    def _connect(self):
        raise NotImplementedError

    @abstractmethod
    def _list_containers(self):
        """Returns all existing container names"""
        raise NotImplementedError

    @abstractmethod
    def _download(self):
        raise NotImplementedError

    @staticmethod
    def _untar(file_path, dest_path):
        try:
            with tarfile.open(file_path) as t:
                t.extractall(path=dest_path)
            os.remove(file_path)
            # We need to delete our temp tar file
        except tarfile.ReadError:
            raise Exception("Couldn't read fetched file")
        except IOError:
            raise Exception("Tar'ed fetched file couldn't deleted try to delete manually")


class UnixSocketFetcher(IFetcher):
    """Fetcher with UnixSocket module"""

    def __init__(self, src_container, src_path, dest_path, buffer_len):
        super().__init__(src_container, src_path, dest_path, buffer_len)
        msg = ("\nTrying to connect Docker Container named : {}\n"
        "to fetch {} with fixed buffer as {} using {} module\n".format(self.srcContainer,
                                                                     self.srcPath,
                                                                     self.bufferLen,
                                                                     "requests_unixsocket"))
        print(msg)

        _temp = __import__('io', globals(), locals(), ['StringIO'], 0)
        self.json = __import__("json")
        self.stringIO = _temp.StringIO
        self.requests_unixsocket = __import__("requests_unixsocket")
        self._session = None
        self._connect()
        if src_container not in self._list_containers():
            raise Exception("The source container doesn't exist")
        self._download()

    def _connect(self):
        self._session = self.requests_unixsocket.Session()

    def _list_containers(self):
        """Returns all existing container names"""
        response = self._session.get("http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/json?all=1")
        if not response.ok:
            raise Exception("Couldn't get Containers list. Check if your docker daemon alive or not")

        strio = self.stringIO(response.text)
        json_response = self.json.load(strio)
        lst_containers = [str(container["Names"])[3:-2] for container in json_response]
        return lst_containers

    def _download(self):
        fd, file_path_with_randomname = mkstemp(suffix=".tar")
        # We need to be sure not to write our tar file on any other file
        response = self._session.get("http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/{}/archive?path={}".format(self.srcContainer,
                                                                                                                   self.srcPath)
                                     ,stream=True)
        if not response.ok:
            if (response.status_code == 404):
                raise Exception("There isn't any file/path like that on container")
            else:
                raise Exception("There was something went wrong\n Status Code : {}".format(response.status_code))

        with open(file_path_with_randomname, "wb") as  file_in_local:
            for chunk in response.iter_content(self.bufferLen):
                file_in_local.write(chunk)
        self._untar(file_path_with_randomname, self.destPath)
        # Now we might overwrite any file if there downloaded file have same name


class DockerPyFetcher(IFetcher):
    """Fetcher with DockerPy module"""

    def __init__(self, src_container, src_path, dest_path, buffer_len):
        super().__init__(src_container, src_path, dest_path, buffer_len)
        msg = ("\nTrying to connect Docker Container named : {}\n"
        "to fetch {} with fixed buffer as {} using {} module\n".format(self.srcContainer,
                                                                     self.srcPath,
                                                                     self.bufferLen,
                                                                     "DockerPy"))
        print(msg)
        self.docker = __import__("docker")
        self._session = None
        self._connect()
        if src_container not in self._list_containers():
            raise Exception("The source container doesn't exist")
        self._download()

    def _connect(self):
        self._session = self.docker.from_env()

    def _list_containers(self):
        """Returns all existing container names"""
        lst_containers = [container.name for container in self._session.containers.list("all=1")]
        return lst_containers

    def _download(self):
        fd, file_path_with_randomname = mkstemp(suffix=".tar")
        # We need to be sure not to write our tar file on any other file

        container = self._session.containers.get("test")
        # Accessing related container

        try:
            file_from_container, stat = container.get_archive(self.srcPath)
        except self.docker.errors.APIError as e:
            if (e.response.status_code == 404):
                raise Exception("There isn't any file/path like that on container")
            else:
                raise e

        with open(file_path_with_randomname, "wb") as file_in_local:
            while True:
                buf = file_from_container.read(self.bufferLen)
                if not buf:
                    break
                file_in_local.write(buf)
        self._untar(file_path_with_randomname, self.destPath)
        # Now we might overwrite any file if there downloaded file have same name


class DockerCPHelper(object):
    def __init__(self, fetcher):
        if not isinstance(fetcher, IFetcher):
            raise Exception('Bad interface')
        self._fetcher = fetcher

    def download(self):
        self._fetcher._download()

    def list_containers(self):
        return self._fetcher._list_containers()


class DockerCP(object):
    def __init__(self, src_container, src_path, dest_path, buffer_len):
        if find_spec("docker"):
            DockerCPHelper(DockerPyFetcher(src_container, src_path, dest_path, buffer_len))
        elif find_spec("requests_unixsocket"):
            DockerCPHelper(UnixSocketFetcher(src_container, src_path, dest_path, buffer_len))
        else:
            raise Exception("Couldn't find proper Interface for connecting Docker\nTry to install dockerpy or requests_unixsocket python modules")
