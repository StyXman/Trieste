/*
    FUSE: Filesystem in Userspace
    Copyright (C) 2001  Miklos Szeredi (mszeredi@inf.bme.hu)

    This program can be distributed under the terms of the GNU LGPL.
    See the file COPYING.LIB.
*/

#ifndef _FUSE_H_
#define _FUSE_H_

/* This file defines the library interface of FUSE */

/* Now and forever: this interface uses 64 bit off_t */
#define _FILE_OFFSET_BITS 64

#include <sys/types.h>
#include <sys/stat.h>
#include <utime.h>

#include <linux/fuse.h>

/* ----------------------------------------------------------- *
 * Basic FUSE API                                              *
 * ----------------------------------------------------------- */

/** Handle for a FUSE filesystem */
struct fuse;

/* Statfs structure used by FUSE */
struct fuse_statfs {
    long block_size;
    long blocks;
    long blocks_free;
    long files;
    long files_free;
    long namelen;
};

/** Handle for a getdir() operation */
typedef struct fuse_dirhandle *fuse_dirh_t;

/** Function to add an entry in a getdir() operation */
typedef int (*fuse_dirfil_t) (fuse_dirh_t, const char *, int type);

typedef unsigned long fino_t;

/**
 * The file system operations:
 *
 * Most of these should work very similarly to the well known UNIX
 * file system operations.  Exceptions are:
 *
 *  - All operations should return the negated error value (-errno) on
 *  error.
 *
 *  - Getattr() doesn't need to fill in the following fields:
 *      st_ino
 *      st_dev
 *      st_blksize
 *
 *  - readlink() should fill the buffer with a null terminated string.  The
 *  buffer size argument includes the space for the terminating null
 *  character.  If the linkname is too long to fit in the buffer, it should
 *  be truncated.  The return value should be 0 for success.
 *
 *  - getdir() is the opendir(), readdir(), ..., closedir() sequence
 *  in one call. For each directory entry the filldir parameter should
 *  be called.
 *
 *  - There is no create() operation, mknod() will be called for
 *  creation of all non directory, non symlink nodes.
 *
 *  - open() should not return a filehandle, but 0 on success.  No
 *  creation, or trunctation flags (O_CREAT, O_EXCL, O_TRUNC) will be
 *  passed to open().  Open should only check if the operation is
 *  permitted for the given flags.
 *
 *  - read(), write() are not passed a filehandle, but rather a
 *  pathname.  The offset of the read and write is passed as the last
 *  argument, like the pread() and pwrite() system calls.
 *
 *  - release() is called when an open file has:
 *       1) all file descriptors closed
 *       2) all memory mappings unmapped
 *    This call need only be implemented if this information is required,
 *    otherwise set this function to NULL.
 *
 */
struct fuse_operations {
    int (*lookup)   (fino_t, const char *, struct stat *);
    int (*getattr)  (fino_t, struct stat *);
    int (*setattr)  (fino_t, unsigned int, struct fuse_attr *, struct stat *);
    int (*readlink) (fino_t, char *, size_t);
    int (*getdir)   (fino_t, fuse_dirh_t, fuse_dirfil_t);
    // returns the ino if ok
    int (*mknod)    (fino_t, const char *, mode_t, dev_t);
    int (*mkdir)    (fino_t, const char *, mode_t);
    int (*unlink)   (fino_t, const char *);
    int (*rmdir)    (fino_t, const char *);
    int (*symlink)  (fino_t, const char *, const char *);
    int (*rename)   (fino_t, const char *, fino_t, const char *);
    int (*link)     (fino_t, const char *, fino_t);
    int (*chmod)    (fino_t, mode_t);
    int (*chown)    (fino_t, uid_t, gid_t);
    int (*truncate) (fino_t, off_t);
    int (*utime)    (fino_t, struct utimbuf *);
    int (*open)     (fino_t, int);
    int (*read)     (fino_t, char *, size_t, off_t);
    int (*write)    (fino_t, const char *, size_t, off_t);
    int (*statfs)   (struct fuse_statfs *);
    int (*release)  (fino_t, int);
};

/** Extra context that may be needed by some filesystems */
struct fuse_context {
    uid_t uid;
    gid_t gid;
};

/* FUSE flags: */

/** Enable debuging output */
#define FUSE_DEBUG       (1 << 1)

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Create a FUSE mountpoint
 *
 * Returns a control file descriptor suitable for passing to
 * fuse_new()
 *
 * @param mountpoint the mount point path
 * @param args array of arguments to be passed to fusermount (NULL
 *        terminated).  Can be NULL if no arguments are needed.
 * @return the control file descriptor on success, -1 on failure
 */
int fuse_mount(const char *mountpoint, const char *args[]);

/*
 * Umount a FUSE mountpoint
 *
 * @param mountpoint the mount point path
 */
void fuse_unmount(const char *mountpoint);

/**
 * Create a new FUSE filesystem.
 *
 * @param fd the control file descriptor
 * @param flags any combination of the FUSE flags defined above, or 0
 * @param op the operations
 * @return the created FUSE handle
 */
struct fuse *fuse_new(int fd, int flags, const struct fuse_operations *op);

/**
 * Destroy the FUSE handle.
 *
 * The filesystem is not unmounted.
 *
 * @param f the FUSE handle
 */
void fuse_destroy(struct fuse *f);

/**
 * FUSE event loop.
 *
 * Requests from the kernel are processed, and the apropriate
 * operations are called.
 *
 * @param f the FUSE handle
 */
void fuse_loop(struct fuse *f);


/**
 * Exit from event loop
 *
 * @param f the FUSE handle
 */
void fuse_exit(struct fuse *f);

/**
 * FUSE event loop with multiple threads
 *
 * Requests from the kernel are processed, and the apropriate
 * operations are called.  Request are processed in parallel by
 * distributing them between multiple threads.
 *
 * Calling this function requires the pthreads library to be linked to
 * the application.
 *
 * @param f the FUSE handle
 */
void fuse_loop_mt(struct fuse *f);

/**
 * Get the current context
 *
 * The context is only valid for the duration of a filesystem
 * operation, and thus must not be stored and used later.
 *
 * @param f the FUSE handle
 * @return the context
 */
struct fuse_context *fuse_get_context(struct fuse *f);

/* ----------------------------------------------------------- *
 * Miscellaneous helper fuctions                               *
 * ----------------------------------------------------------- */

/*
 * Main function of FUSE.
 *
 * This is for the lazy.  This is all that has to be called from the
 * main() function.
 *
 * This function does the following:
 *   - mounts the filesystem
 *   - installs signal handlers for INT, HUP, TERM and PIPE
 *   - registers an exit handler to unmount the filesystem on program exit
 *   - parses command line options (-d -s and -h)
 *   - creates a fuse handle
 *   - registers the operations
 *   - calls either the single-threaded or the multi-threaded event loop
 *
 * @param argc the argument counter passed to the main() function
 * @param argv the argument vector passed to the main() function
 * @param op the file system operation
 */
void fuse_main(int argc, char *argv[], const struct fuse_operations *op);

/* ----------------------------------------------------------- *
 * Advanced API for event handling, don't worry about this...  *
 * ----------------------------------------------------------- */

struct fuse_cmd;
typedef void (*fuse_processor_t)(struct fuse *, struct fuse_cmd *, void *);
struct fuse_cmd *__fuse_read_cmd(struct fuse *f);
void __fuse_process_cmd(struct fuse *f, struct fuse_cmd *cmd);
void __fuse_loop_mt(struct fuse *f, fuse_processor_t proc, void *data);

#ifdef __cplusplus
}
#endif

#endif /* _FUSE_H_ */
