import os
import re
import zlib

__author__ = 'byeongal'
__version__ = 'alpha'

class PDFParser:
    re_pdfheader = re.compile(rb'%PDF-1.\d+', re.IGNORECASE)
    re_object = re.compile(rb'\d+\s+\d+\s+obj[\s\S]*?endobj', re.IGNORECASE)

    def __init__(self, name=None, data=None):
        if name is None and data is None:
            raise ValueError('Must supply either name or data')
        self.__parse__(name, data)

    def __parse__(self, name, data):
        if data is None:
            stat = os.stat(name)
            if stat.st_size == 0:
                raise PDFFormatError('The file is empty.')
            try :
                with open(name, 'rb') as f:
                    data = f.read()
            except IOError as excp:
                exception_msg = f'{excp}'
                raise Exception(f'Unable to access file \'{name}\' : {exception_msg}')
        result = PDFParser.re_pdfheader.match(data)
        if result is None:
            raise PDFFormatError('PDFHeader does not exist.')
        self.file_size = len(data)
        self.pdf_version = result.group().split(b'-')[-1].decode()
        self.objs = list()
        for each_object in PDFParser.re_object.finditer(data):
            self.objs.append(ObjectStructure(each_object.group()))

    def dump_dict(self):
        ret = dict()
        ret['File Size'] = self.file_size
        ret['PDF Version'] = self.pdf_version
        ret['Objects'] = list()
        for obj in self.objs:
            ret['Objects'].append(obj.dump_dict())
        return ret

    def get_hash(self):
        pass


class PDFFormatError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class ObjectStructure:
    re_filter = re.compile(rb'/Filter\s+/(\w+)', re.IGNORECASE)
    re_stream = re.compile(rb'stream\s*[\s\S]*?\s*endstream', re.IGNORECASE)
    re_reference = re.compile(rb'\d+\s+\d+\s+R')
    def __init__(self, object_data):
        self.object_data = object_data
        self.__parse__()

    def __parse__(self):
        self.object_id = int(self.object_data.split()[0].decode())
        self.reference_id_list = list()
        for ref in ObjectStructure.re_reference.finditer(self.object_data):
            object_id = ref.group().split()[0]
            self.reference_id_list.append(int(object_id.decode()))
        filter = ObjectStructure.re_filter.search(self.object_data)
        if filter is not None:
            encoding_type = filter.groups()[0].decode().lower()
            stream = ObjectStructure.re_stream.search(self.object_data).group()[6:-9]
            stream = stream.strip()
            if encoding_type == 'flatedecode':
                try:
                    stream = zlib.decompress(stream)
                except zlib.error:
                    pass
            elif encoding_type == 'asciihexdecode':
                pass
            elif encoding_type == 'ascii85decode':
                pass
            elif encoding_type == 'lzwdecode':
                pass
            elif encoding_type == 'runlengthdecode':
                pass
            self.stream = stream

    def dump_dict(self):
        ret = dict()
        ret['ObjectID'] = self.object_id
        ret['Referencing'] = self.reference_id_list
        if hasattr(self, 'stream'):
            ret['Stream'] = self.stream
        return ret