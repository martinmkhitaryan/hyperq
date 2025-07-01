# distutils: language=c++

from libcpp.string cimport string
from libcpp cimport bool
from libc.stdlib cimport free
from cpython.bytes cimport PyBytes_FromStringAndSize, PyBytes_AsStringAndSize
import cython

import ctypes
from multiprocessing import context


cdef extern from "hyperq.hpp":
    cdef cppclass _HyperQ "HyperQ":
        _HyperQ(size_t capacity, const string& name) except +
        _HyperQ(const string& name) except +
        bool empty() except +
        bool full() except +
        size_t size() except +
        size_t get_buffer_size() except +
        size_t available() except +
        void clear() except +
        const string& get_shm_name() except +
        int get_shm_fd() except +
        void put(const char* data, size_t len) except +
        char* get(size_t& message_size) except +

cdef class HyperQ:
    cdef _HyperQ* _buffer
    cdef object _loads_func
    cdef object _dumps_func
    
    def __cinit__(self, capacity_or_name, name=None):
        """
        Initialize a circular buffer.
        
        Args:
            capacity_or_name: Either an integer capacity (for creating new buffer) 
                             or a string name (for attaching to existing buffer)
            name: Name for shared memory (max 28 characters, required when creating)
        """
        cdef string cpp_name
        
        self._loads_func = context.reduction.ForkingPickler.loads
        self._dumps_func = context.reduction.ForkingPickler.dumps
        
        if isinstance(capacity_or_name, int):
            if capacity_or_name <= 0:
                raise ValueError("Capacity must be greater than 0")
            
            if name is None:
                raise ValueError("name must be provided when creating new queue")
            
            if len(name) > 28:
                raise ValueError("name must be at most 28 characters long")
            
            self._buffer = new _HyperQ(<size_t>capacity_or_name, name.encode('utf-8'))
        elif isinstance(capacity_or_name, str):
            cpp_name = capacity_or_name.encode('utf-8')
            self._buffer = new _HyperQ(cpp_name)
        else:
            raise TypeError("capacity_or_name must be int or str")
    
    def __dealloc__(self):
        if self._buffer != NULL:
            del self._buffer
    

    def loads(self, msg_bytes):
        return self._loads_func(msg_bytes)
    
    def dumps(self, obj):
        return self._dumps_func(obj).tobytes()
    
    def put(self, data) -> None:
        cdef:
            char* data_ptr
            Py_ssize_t data_len
        
        # Optimize for bytes: avoid serialization overhead
        if isinstance(data, bytes):
            PyBytes_AsStringAndSize(data, &data_ptr, &data_len)
        else:
            # Serialize non-bytes objects
            data = self.dumps(data)   
            PyBytes_AsStringAndSize(data, &data_ptr, &data_len)     
        
        self._buffer.put(data_ptr, data_len)
    
    def get(self):
        cdef:
            char* data_ptr = NULL
            size_t message_size = 0
        
        try:
            data_ptr = self._buffer.get(message_size)
            
            if data_ptr != NULL:
                msg_bytes = PyBytes_FromStringAndSize(data_ptr, message_size)
                try:
                    return self.loads(msg_bytes)
                except:
                    return msg_bytes
            else:
                raise RuntimeError("Unexpected failure in get()")
        finally:
            if data_ptr != NULL:
                free(data_ptr)
    
    @property
    def empty(self):
        return self._buffer.empty()
    
    @property
    def full(self):
        return self._buffer.full()
    
    @property
    def size(self):
        return self._buffer.size()
    
    @property
    def buffer_size(self):
        return self._buffer.get_buffer_size()
    
    @property
    def available(self):
        return self._buffer.available()
    
    def clear(self):
        self._buffer.clear()
    
    @property
    def shm_name(self):
        return self._buffer.get_shm_name().decode('utf-8')
    
    @property
    def shm_fd(self):
        return self._buffer.get_shm_fd()
    
    def __len__(self):
        return self.size
    
    def __bool__(self):
        return not self.empty
    
    def __repr__(self):
        return f"HyperQ(capacity={self.buffer_size}, size={self.size}, empty={self.empty}, full={self.full})" 


cdef class BytesHyperQ:
    cdef _HyperQ* _buffer
    
    def __cinit__(self, capacity_or_name, name=None):
        """
        Initialize a bytes-optimized circular buffer.
        
        Args:
            capacity_or_name: Either an integer capacity (for creating new buffer) 
                             or a string name (for attaching to existing buffer)
            name: Name for shared memory (max 28 characters, required when creating)
        """
        cdef string cpp_name
        
        if isinstance(capacity_or_name, int):
            if capacity_or_name <= 0:
                raise ValueError("Capacity must be greater than 0")
            
            if name is None:
                raise ValueError("name must be provided when creating new queue")
            
            if len(name) > 28:
                raise ValueError("name must be at most 28 characters long")
            
            self._buffer = new _HyperQ(<size_t>capacity_or_name, name.encode('utf-8'))
        elif isinstance(capacity_or_name, str):
            cpp_name = capacity_or_name.encode('utf-8')
            self._buffer = new _HyperQ(cpp_name)
        else:
            raise TypeError("capacity_or_name must be int or str")
    
    def __dealloc__(self):
        if self._buffer != NULL:
            del self._buffer
    
    def put(self, bytes data) -> None:
        cdef:
            char* data_ptr
            Py_ssize_t data_len
        
        PyBytes_AsStringAndSize(data, &data_ptr, &data_len)
        self._buffer.put(data_ptr, data_len)
    
    def get(self) -> bytes:
        cdef:
            char* data_ptr = NULL
            size_t message_size = 0
        
        try:
            data_ptr = self._buffer.get(message_size)
            
            if data_ptr != NULL:
                return PyBytes_FromStringAndSize(data_ptr, message_size)
            else:
                raise RuntimeError("Unexpected failure in get()")
        finally:
            if data_ptr != NULL:
                free(data_ptr)
    
    @property
    def empty(self):
        return self._buffer.empty()
    
    @property
    def full(self):
        return self._buffer.full()
    
    @property
    def size(self):
        return self._buffer.size()
    
    @property
    def buffer_size(self):
        return self._buffer.get_buffer_size()
    
    @property
    def available(self):
        return self._buffer.available()
    
    def clear(self):
        self._buffer.clear()
    
    @property
    def shm_name(self):
        return self._buffer.get_shm_name().decode('utf-8')
    
    @property
    def shm_fd(self):
        return self._buffer.get_shm_fd()
    
    def __len__(self):
        return self.size
    
    def __bool__(self):
        return not self.empty
    
    def __repr__(self):
        return f"BytesHyperQ(capacity={self.buffer_size}, size={self.size}, empty={self.empty}, full={self.full})" 