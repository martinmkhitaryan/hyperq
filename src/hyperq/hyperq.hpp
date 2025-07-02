#ifndef HYPERQ_HPP
#define HYPERQ_HPP

#include <string>
#include <stdexcept>
#include <cstring>
#include <cstdio>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <pthread.h>
#include <time.h>
#include <errno.h>

constexpr size_t page_align(size_t n, size_t pagesize)
{
    return (n + pagesize - 1) & ~(pagesize - 1);
}

struct SharedQueueHeader
{
    size_t head;
    size_t tail;
    size_t size_;
    size_t buffer_size;
    
    // Reference counting for shared memory cleanup
    size_t ref_count;

    pthread_mutex_t mutex;
    pthread_cond_t not_empty;
    pthread_cond_t not_full;
    
    char buffer_shm_name[32];
};

class HyperQ
{
private:
    SharedQueueHeader *header;
    char *buffer;
    size_t buffer_size;
    int shm_fd;
    int buffer_shm_fd;
    std::string shm_name;
    std::string buffer_shm_name;
    size_t header_size;

    void init_sync_objects()
    {
        pthread_mutexattr_t mutex_attr;
        pthread_condattr_t cond_attr;

        pthread_mutexattr_init(&mutex_attr);
        pthread_mutexattr_setpshared(&mutex_attr, PTHREAD_PROCESS_SHARED);
        pthread_mutex_init(&header->mutex, &mutex_attr);
        pthread_mutexattr_destroy(&mutex_attr);

        pthread_condattr_init(&cond_attr);
        pthread_condattr_setpshared(&cond_attr, PTHREAD_PROCESS_SHARED);
        pthread_cond_init(&header->not_empty, &cond_attr);
        pthread_cond_init(&header->not_full, &cond_attr);
        pthread_condattr_destroy(&cond_attr);
    }

    void map_header()
    {
        header = static_cast<SharedQueueHeader *>(
            mmap(nullptr, header_size, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0));
        if (header == MAP_FAILED) [[unlikely]]
        {
            throw std::runtime_error("mmap header failed: " + std::string(strerror(errno)));
        }
    }

    void setup_virtual_memory(size_t buffer_sz)
    {
        buffer = static_cast<char *>(mmap(nullptr, 2 * buffer_sz, PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0));
        if (buffer == MAP_FAILED) [[unlikely]]
        {
            throw std::runtime_error("mmap virtual space failed: " + std::string(strerror(errno)) + " (size=" + std::to_string(2 * buffer_sz) + ")");
        }

        void *first_half = mmap(buffer, buffer_sz, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_FIXED, buffer_shm_fd, 0);
        if (first_half == MAP_FAILED) [[unlikely]]
        {
            munmap(buffer, 2 * buffer_sz);
            throw std::runtime_error("mmap first half failed: " + std::string(strerror(errno)) + " (size=" + std::to_string(buffer_sz) + ")");
        }

        void *second_half = mmap(buffer + buffer_sz, buffer_sz, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_FIXED, buffer_shm_fd, 0);
        if (second_half == MAP_FAILED) [[unlikely]]
        {
            munmap(buffer, 2 * buffer_sz);
            throw std::runtime_error("mmap second half failed: " + std::string(strerror(errno)) + " (size=" + std::to_string(buffer_sz) + ")");
        }
    }

    void init_header()
    {
        header_size = page_align(sizeof(SharedQueueHeader), getpagesize());
    }

    void setup_buffer()
    {
        const size_t buffer_sz = page_align(buffer_size, getpagesize());
        setup_virtual_memory(buffer_sz);
    }

public:
    HyperQ(size_t cap, const std::string &name)
    {
        if (cap == 0) [[unlikely]]
        {
            throw std::invalid_argument("Capacity must be greater than 0");
        }

        
        init_header();

        buffer_size = page_align(cap, getpagesize());

        shm_name = name;
        char buffer_name[32];
        snprintf(buffer_name, sizeof(buffer_name), "/b_%s", shm_name.c_str());
        buffer_shm_name = buffer_name;

        shm_fd = shm_open(shm_name.c_str(), O_CREAT | O_RDWR, 0666);
        if (shm_fd == -1) [[unlikely]]
        {
            throw std::runtime_error("shm_open header failed: " + std::string(strerror(errno)));
        }

        if (ftruncate(shm_fd, header_size) == -1) [[unlikely]]
        {
            close(shm_fd);
            shm_unlink(shm_name.c_str());
            throw std::runtime_error("ftruncate header failed: " + std::string(strerror(errno)) + " (size=" + std::to_string(header_size) + ")");
        }

        buffer_shm_fd = shm_open(buffer_name, O_CREAT | O_RDWR, 0666);
        if (buffer_shm_fd == -1) [[unlikely]]
        {
            close(shm_fd);
            shm_unlink(shm_name.c_str());
            throw std::runtime_error("shm_open buffer failed: " + std::string(strerror(errno)));
        }

        if (ftruncate(buffer_shm_fd, buffer_size) == -1) [[unlikely]]
        {
            close(shm_fd);
            close(buffer_shm_fd);
            shm_unlink(shm_name.c_str());
            shm_unlink(buffer_name);
            throw std::runtime_error("ftruncate buffer failed: " + std::string(strerror(errno)) + " (size=" + std::to_string(buffer_size) + ")");
        }

        map_header();

        header->head = 0;
        header->tail = 0;
        header->size_ = 0;
        header->buffer_size = buffer_size;
        header->ref_count = 1;  // First instance
        strncpy(header->buffer_shm_name, buffer_name, sizeof(header->buffer_shm_name) - 1);
        header->buffer_shm_name[sizeof(header->buffer_shm_name) - 1] = '\0';

        init_sync_objects();
        setup_buffer();
    }

    HyperQ(const std::string &name)
    {
        shm_name = name;

        shm_fd = shm_open(shm_name.c_str(), O_RDWR, 0666);
        if (shm_fd == -1) [[unlikely]]
        {
            throw std::runtime_error("shm_open header failed");
        }

        init_header();
        map_header();
        buffer_size = header->buffer_size;
        buffer_shm_name = header->buffer_shm_name;

        buffer_shm_fd = shm_open(buffer_shm_name.c_str(), O_RDWR, 0666);
        if (buffer_shm_fd == -1) [[unlikely]]
        {
            close(shm_fd);
            throw std::runtime_error("shm_open buffer failed");
        }

        // Increment reference count atomically
        pthread_mutex_lock(&header->mutex);
        header->ref_count++;
        pthread_mutex_unlock(&header->mutex);

        setup_buffer();
    }

    ~HyperQ()
    {
        if (header != nullptr)
        {
            const size_t buffer_sz = page_align(buffer_size, getpagesize());

            if (buffer != nullptr)
            {
                munmap(buffer, 2 * buffer_sz);
            }

            // Check reference count before unmapping header
            bool should_unlink = false;
            pthread_mutex_lock(&header->mutex);
            header->ref_count--;
            should_unlink = (header->ref_count == 0);
            size_t final_ref_count = header->ref_count;
            pthread_mutex_unlock(&header->mutex);
            
            munmap(header, header_size);
            close(shm_fd);
            close(buffer_shm_fd);

            if (should_unlink)
            {
                shm_unlink(shm_name.c_str());
                shm_unlink(buffer_shm_name.c_str());
            }
        }
    }

    HyperQ(const HyperQ &) = delete;
    HyperQ &operator=(const HyperQ &) = delete;

    HyperQ(HyperQ &&other) noexcept
        : header(other.header), buffer(other.buffer), buffer_size(other.buffer_size),
          shm_fd(other.shm_fd), buffer_shm_fd(other.buffer_shm_fd),
          shm_name(std::move(other.shm_name)), buffer_shm_name(std::move(other.buffer_shm_name)),
          header_size(other.header_size)
    {
        other.header = nullptr;
        other.buffer = nullptr;
        other.shm_fd = -1;
        other.buffer_shm_fd = -1;
    }

    HyperQ &operator=(HyperQ &&other) noexcept
    {
        if (this != &other)
        {
            this->~HyperQ();
            header = other.header;
            buffer = other.buffer;
            buffer_size = other.buffer_size;
            shm_fd = other.shm_fd;
            buffer_shm_fd = other.buffer_shm_fd;
            shm_name = std::move(other.shm_name);
            buffer_shm_name = std::move(other.buffer_shm_name);
            header_size = other.header_size;
            other.header = nullptr;
            other.buffer = nullptr;
            other.shm_fd = -1;
            other.buffer_shm_fd = -1;
        }
        return *this;
    }

    const std::string &get_shm_name() const
    {
        return shm_name;
    }

    int get_shm_fd() const
    {
        return shm_fd;
    }

    void put(const char *data, size_t len)
    {
        if (len == 0) [[unlikely]]
        {
            return;
        }

        pthread_mutex_lock(&header->mutex);
        
        while (len + sizeof(size_t) >= buffer_size - header->size_)
        {
            pthread_cond_wait(&header->not_full, &header->mutex);
        }

        memcpy(buffer + header->tail, &len, sizeof(size_t));
        header->tail = (header->tail + sizeof(size_t)) % buffer_size;

        memcpy(buffer + header->tail, data, len);
        header->tail = (header->tail + len) % buffer_size;
        header->size_ += len + sizeof(size_t);

        pthread_cond_signal(&header->not_empty);
        pthread_mutex_unlock(&header->mutex);
    }

    char* get(size_t &message_size)
    {
        pthread_mutex_lock(&header->mutex);
        
        while (header->size_ == 0)
        {
            pthread_cond_wait(&header->not_empty, &header->mutex);
        }

        memcpy(&message_size, buffer + header->head, sizeof(size_t));
        header->head = (header->head + sizeof(size_t)) % buffer_size;

        char* data = static_cast<char*>(malloc(message_size));
        if (!data) [[unlikely]] {
            pthread_mutex_unlock(&header->mutex);
            return nullptr;
        }

        memcpy(data, buffer + header->head, message_size);
        header->head = (header->head + message_size) % buffer_size;
        header->size_ -= message_size + sizeof(size_t);

        pthread_cond_signal(&header->not_full);
        pthread_mutex_unlock(&header->mutex);
        return data;
    }

    bool empty() const
    {
        pthread_mutex_lock(&const_cast<pthread_mutex_t &>(header->mutex));
        bool result = header->size_ == 0;
        pthread_mutex_unlock(&const_cast<pthread_mutex_t &>(header->mutex));
        return result;
    }

    bool full() const
    {
        pthread_mutex_lock(&const_cast<pthread_mutex_t &>(header->mutex));
        bool result = header->size_ >= buffer_size;
        pthread_mutex_unlock(&const_cast<pthread_mutex_t &>(header->mutex));
        return result;
    }

    size_t size() const
    {
        pthread_mutex_lock(&const_cast<pthread_mutex_t &>(header->mutex));
        size_t result = header->size_;
        pthread_mutex_unlock(&const_cast<pthread_mutex_t &>(header->mutex));
        return result;
    }

    size_t get_buffer_size() const
    {
        return buffer_size;
    }

    size_t available() const
    {
        pthread_mutex_lock(&const_cast<pthread_mutex_t &>(header->mutex));
        size_t result = buffer_size - header->size_;
        pthread_mutex_unlock(&const_cast<pthread_mutex_t &>(header->mutex));
        return result;
    }

    void clear()
    {
        pthread_mutex_lock(&header->mutex);
        header->head = 0;
        header->tail = 0;
        header->size_ = 0;
        pthread_cond_broadcast(&header->not_full);
        pthread_mutex_unlock(&header->mutex);
    }
};

#endif // HYPERQ_HPP