/*
    FUSE: Filesystem in Userspace
    Copyright (C) 2001  Miklos Szeredi (mszeredi@inf.bme.hu)

    This program can be distributed under the terms of the GNU GPL.
    See the file COPYING.
*/

#include "fuse_i.h"

#include <linux/pagemap.h>
#include <linux/sched.h>
#include <linux/slab.h>
#include <linux/file.h>
#include <linux/proc_fs.h>

#include <consts.h>

#define FUSE_SUPER_MAGIC 0x65735546

static void fuse_read_inode(struct inode *inode)
{
	/* No op */
}

static void fuse_clear_inode(struct inode *inode)
{
	struct fuse_conn *fc = INO_FC(inode);
	struct fuse_in *in = NULL;
	struct fuse_forget_in *inarg = NULL;

	if(fc == NULL)
		return;

	in = kmalloc(sizeof(struct fuse_in), GFP_NOFS);
	if(!in)
		return;
	memset(in, 0, sizeof(struct fuse_in));

	inarg = kmalloc(sizeof(struct fuse_forget_in), GFP_NOFS);
	if(!inarg)
		goto out_free;

	memset(inarg, 0, sizeof(struct fuse_forget_in));
	inarg->version = inode->i_version;

	in->h.opcode = FUSE_FORGET;
	in->h.ino = inode->i_ino;
	in->numargs = 1;
	in->args[0].size = sizeof(struct fuse_forget_in);
	in->args[0].value = inarg;

	if(!request_send_noreply(fc, in))
		return;

  out_free:
	kfree(inarg);
	kfree(in);
}

static void fuse_put_super(struct super_block *sb)
{
	struct fuse_conn *fc = sb->u.generic_sbp;

	spin_lock(&fuse_lock);
	fc->sb = NULL;
	fc->uid = 0;
	fc->flags = 0;
	/* Flush all readers on this fs */
	wake_up_all(&fc->waitq);
	fuse_release_conn(fc);
	sb->u.generic_sbp = NULL;
	spin_unlock(&fuse_lock);
}

static void convert_fuse_statfs(struct statfs *stbuf, struct fuse_kstatfs *attr)
{
	stbuf->f_type    = FUSE_SUPER_MAGIC;
	stbuf->f_bsize   = attr->block_size;
	stbuf->f_blocks  = attr->blocks;
	stbuf->f_bfree   = stbuf->f_bavail = attr->blocks_free;
	stbuf->f_files   = attr->files;
	stbuf->f_ffree   = attr->files_free;
	/* Is this field necessary?  Most filesystems ignore it...
	stbuf->f_fsid.val[0] = (FUSE_SUPER_MAGIC>>16)&0xffff;
	stbuf->f_fsid.val[1] =  FUSE_SUPER_MAGIC     &0xffff; */
	stbuf->f_namelen = attr->namelen;
}

static int fuse_statfs(struct super_block *sb, struct statfs *st)
{
	struct fuse_conn *fc = sb->u.generic_sbp;
	struct fuse_in in = FUSE_IN_INIT;
	struct fuse_out out = FUSE_OUT_INIT;
	struct fuse_statfs_out outarg;

	in.numargs = 0;
	in.h.opcode = FUSE_STATFS;
	out.numargs = 1;
	out.args[0].size = sizeof(outarg);
	out.args[0].value = &outarg;
	request_send(fc, &in, &out);
	if(!out.h.error)
		convert_fuse_statfs(st,&outarg.st);

	return out.h.error;
}

static struct super_operations fuse_super_operations = {
	read_inode:	fuse_read_inode,
	clear_inode:	fuse_clear_inode,
	put_super:	fuse_put_super,
	statfs: fuse_statfs,
};


static struct fuse_conn *get_conn(struct fuse_mount_data *d)
{
	struct fuse_conn *fc = NULL;
	struct file *file;
	struct inode *ino;

	if(d == NULL) {
		printk("fuse_read_super: Bad mount data\n");
		return NULL;
	}

	if(d->version != FUSE_KERNEL_VERSION) {
		printk("fuse_read_super: Bad version: %i\n", d->version);
		return NULL;
	}

	file = fget(d->fd);
	ino = NULL;
	if(file)
		ino = file->f_dentry->d_inode;

	if(!ino || !proc_fuse_dev || proc_fuse_dev->low_ino != ino->i_ino) {
		printk("fuse_read_super: Bad file: %i\n", d->fd);
		goto out;
	}

	fc = file->private_data;

  out:
	fput(file);
	return fc;

}

static struct inode *get_root_inode(struct super_block *sb, unsigned int mode)
{
	struct fuse_attr attr;
	memset(&attr, 0, sizeof(attr));

	attr.mode = mode;
	return fuse_iget(sb, 1, &attr, 0);
}

static struct super_block *fuse_read_super(struct super_block *sb,
					   void *data, int silent)
{
	struct fuse_conn *fc;
	struct inode *root;
	struct fuse_mount_data *d = data;

        sb->s_blocksize = pageSize;
        sb->s_blocksize_bits = pageSizeBits;
        sb->s_magic = FUSE_SUPER_MAGIC;
        sb->s_op = &fuse_super_operations;

	root = get_root_inode(sb, d->rootmode);
	if(root == NULL) {
		printk("fuse_read_super: failed to get root inode\n");
		return NULL;
	}

	spin_lock(&fuse_lock);
	fc = get_conn(d);
	if(fc == NULL)
		goto err;

	if(fc->sb != NULL) {
		printk("fuse_read_super: connection already mounted\n");
		goto err;
	}

        sb->u.generic_sbp = fc;
	sb->s_root = d_alloc_root(root);
	if(!sb->s_root)
		goto err;

	fc->sb = sb;
	fc->flags = d->flags;
	fc->uid = d->uid;
	spin_unlock(&fuse_lock);

	return sb;

  err:
	spin_unlock(&fuse_lock);
	iput(root);
	return NULL;
}


static DECLARE_FSTYPE(fuse_fs_type, "fuse", fuse_read_super, 0);

int fuse_fs_init()
{
	int res;

	res = register_filesystem(&fuse_fs_type);
	if(res)
		printk("fuse: failed to register filesystem\n");

	return res;
}

void fuse_fs_cleanup()
{
	unregister_filesystem(&fuse_fs_type);
}

/*
 * Local Variables:
 * indent-tabs-mode: t
 * c-basic-offset: 8
 * End:
 */
