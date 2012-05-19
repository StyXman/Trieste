/*
    Copyright (C) 2001  Jeff Epler  <jepler@unpythonic.dhs.org>
                  2004  Marcos DIone <mdione@grulic.org.ar>

    This program can be distributed under the terms of the GNU GPL.
    See the file COPYING.
*/

#include <Python.h>
#include <fuse.h>
#include <time.h>
#include <consts.h>

static PyObject *getattr_cb=NULL, *readlink_cb=NULL, *getdir_cb=NULL,
  *mknod_cb=NULL, *mkdir_cb=NULL, *unlink_cb=NULL, *rmdir_cb=NULL,
  *symlink_cb=NULL, *rename_cb=NULL, *link_cb=NULL, *chmod_cb=NULL,
  *chown_cb=NULL, *truncate_cb=NULL, *utime_cb=NULL,
  *open_cb=NULL, *read_cb=NULL, *write_cb=NULL,
  *lookup_cb=NULL, *statfs_cb=NULL, *setattr_cb=NULL;

#define PROLOGUE \
  int ret = -EINVAL; \
  if (!v) { \
    PyErr_Print(); \
    goto OUT; \
  } \
  if(v == Py_None) { \
    ret = 0; \
    goto OUT_DECREF; \
  } \
  if(PyInt_Check(v)) { \
    ret = PyInt_AsLong(v); \
    goto OUT_DECREF; \
  }

#define EPILOGUE \
  OUT_DECREF: \
    Py_DECREF(v); \
  OUT: \
    return ret;

void py_to_stat (PyObject *v, struct stat *st) {
  st->st_mode = PyInt_AsLong(PyTuple_GetItem(v, 0));
  st->st_ino  = PyLong_AsLong(PyTuple_GetItem(v, 1));
  st->st_dev  = PyLong_AsLong(PyTuple_GetItem(v, 2));
  st->st_nlink= PyInt_AsLong(PyTuple_GetItem(v, 3));
  st->st_uid  = PyInt_AsLong(PyTuple_GetItem(v, 4));
  st->st_gid  = PyInt_AsLong(PyTuple_GetItem(v, 5));
  st->st_size = PyLong_AsLong(PyTuple_GetItem(v, 6));
  st->st_atime= PyInt_AsLong(PyTuple_GetItem(v, 7));
  st->st_mtime= PyInt_AsLong(PyTuple_GetItem(v, 8));
  st->st_ctime= PyInt_AsLong(PyTuple_GetItem(v, 9));

  /* Fill in fields not provided by Python lstat() */
  st->st_blksize= pageSize;
  st->st_blocks= (st->st_size + pageSize-1)/pageSize;
}

static int getattr_func(fino_t ino, struct stat *st)
{
  int i;
  PyObject *v = PyObject_CallFunction(getattr_cb, "i", ino);
  PROLOGUE

  if(!PyTuple_Check(v)) {
    goto OUT_DECREF;
  }
  if(PyTuple_Size(v) < 10) {
    goto OUT_DECREF;
  }
  for(i=0; i<10; i++) {
    if (!PyLong_Check(PyTuple_GetItem(v, i)) && !PyInt_Check(PyTuple_GetItem(v, i))) {
      goto OUT_DECREF;
    }
  }

  py_to_stat (v, st);

  ret = 0;
  EPILOGUE
}

static int readlink_func(fino_t ino, char *link, size_t size)
{
  PyObject *v = PyObject_CallFunction(readlink_cb, "i", ino);
  char *s;
  PROLOGUE

  if(!PyString_Check(v)) { ret = -EINVAL; goto OUT_DECREF; }
  s = PyString_AsString(v);
  strncpy(link, s, size);
  link[size-1] = '\0';
  ret = 0;

  EPILOGUE
}

static int getdir_add_entry(PyObject *w, fuse_dirh_t dh, fuse_dirfil_t df)
{
  PyObject *o0;
  PyObject *o1;
  int ret = -EINVAL;

  if(!PySequence_Check(w)) {
    goto out;
  }
  if(PySequence_Length(w) != 2) {
    goto out;
  }
  o0 = PySequence_GetItem(w, 0);
  o1 = PySequence_GetItem(w, 1);

  if(!PyString_Check(o0)) {
    goto out_decref;
  }
  if(!PyInt_Check(o1)) {
    goto out_decref;
  }

  ret = df(dh, PyString_AsString(o0), PyInt_AsLong(o1));

out_decref:
  Py_DECREF(o0);
  Py_DECREF(o1);

out:
  return ret;
}

static int getdir_func(fino_t ino, fuse_dirh_t dh, fuse_dirfil_t df)
{
  PyObject *v = PyObject_CallFunction(getdir_cb, "i", ino);
  int i;
  PROLOGUE

  if(!PySequence_Check(v)) {
    printf("getdir_func not sequence\n");
    goto OUT_DECREF;
  }
  for(i=0; i < PySequence_Length(v); i++) {
    PyObject *w = PySequence_GetItem(v, i);
    ret = getdir_add_entry(w, dh, df);
    Py_DECREF(w);
    if(ret != 0)
      goto OUT_DECREF;
  }
  ret = 0;

  EPILOGUE
}

static int mknod_func(fino_t ino, const char *name, mode_t m, dev_t d)
{
  PyObject *v = PyObject_CallFunction(mknod_cb, "isi", ino, name, m);
  PROLOGUE

  EPILOGUE
}

static int mkdir_func(fino_t ino, const char *name, mode_t m)
{
  PyObject *v = PyObject_CallFunction(mkdir_cb, "isi", ino, name, m);
  PROLOGUE
  EPILOGUE
}

static int unlink_func(fino_t ino, const char *name)
{
  PyObject *v = PyObject_CallFunction(unlink_cb, "is", ino, name);
  PROLOGUE
  EPILOGUE
}

static int rmdir_func(fino_t ino, const char *name)
{
  PyObject *v = PyObject_CallFunction(rmdir_cb, "is", ino, name);
  PROLOGUE
  EPILOGUE
}

static int symlink_func(fino_t ino, const char *name, const char *path)
{
  PyObject *v = PyObject_CallFunction(symlink_cb, "iss", ino, name, path);
  PROLOGUE
  EPILOGUE
}

static int rename_func(fino_t ino, const char *name, fino_t nino, const char *nname)
{
  PyObject *v = PyObject_CallFunction(rename_cb, "isis", ino, name, nino, nname);
  PROLOGUE
  EPILOGUE
}

static int link_func(fino_t parent, const char *name, fino_t ino)
{
  PyObject *v = PyObject_CallFunction(link_cb, "isi", parent, name, ino);
  PROLOGUE
  EPILOGUE
}

static int setattr_func (fino_t ino, unsigned int mask, struct fuse_attr *attr, struct stat *stat) {
  int i;
  PyObject *tuple= Py_BuildValue ("(llLiii)", attr->atime, attr->mtime, attr->size, attr->mode, attr->uid, attr->gid);
  PyObject *v = PyObject_CallFunction(setattr_cb, "iiO", ino, mask, tuple);
  PROLOGUE
  if(!PyTuple_Check(v)) {
    goto OUT_DECREF;
  }
  if(PyTuple_Size(v) < 10) {
    goto OUT_DECREF;
  }
  for(i=0; i<10; i++) {
    if (!PyLong_Check(PyTuple_GetItem(v, i)) && !PyInt_Check(PyTuple_GetItem(v, i))) {
      goto OUT_DECREF;
    }
  }

  py_to_stat (v, stat);

  ret = 0;
  EPILOGUE
}

static int chmod_func(fino_t ino, mode_t m)
{
  PyObject *v = PyObject_CallFunction(chmod_cb, "ii", ino, m);
  PROLOGUE
  EPILOGUE
}

static int chown_func(fino_t ino, uid_t u, gid_t g)
{
  PyObject *v = PyObject_CallFunction(chown_cb, "iii", ino, u, g);
  PROLOGUE
  EPILOGUE
}

static int truncate_func(fino_t ino, off_t o)
{
  PyObject *v = PyObject_CallFunction(truncate_cb, "ii", ino, o);
  PROLOGUE
  EPILOGUE
}

static int utime_func(fino_t ino, struct utimbuf *u) {
  int actime = u ? u->actime : time(NULL);
  int modtime = u ? u->modtime : actime;
  PyObject *v = PyObject_CallFunction(utime_cb, "i(ii)",
          ino, actime, modtime);
  PROLOGUE
  EPILOGUE
}

static int read_func(fino_t ino, char *buf, size_t s, off_t off)
{
  PyObject *v = PyObject_CallFunction(read_cb, "iii", ino, s, off);
  PROLOGUE
  if(PyString_Check(v)) {
    if(PyString_Size(v) > s) goto OUT_DECREF;
    memcpy(buf, PyString_AsString(v), PyString_Size(v));
    ret = PyString_Size(v);
  }
  EPILOGUE
}

static int write_func(fino_t ino, const char *buf, size_t t, off_t off)
{
  PyObject *v = PyObject_CallFunction(write_cb,"is#i", ino, buf, t, off);
  PROLOGUE
  EPILOGUE
}

static int open_func(fino_t ino, int mode)
{
  PyObject *v = PyObject_CallFunction(open_cb, "ii", ino, mode);
  PROLOGUE
  EPILOGUE
}

static int lookup_func(fino_t ino, const char *name, struct stat *st) {
  int i;

  PyObject *v = PyObject_CallFunction(lookup_cb, "is", ino, name);
  PROLOGUE
  if(!PyTuple_Check(v)) {
    printf ("not tuple\n");
    goto OUT_DECREF;
  }
  if(PyTuple_Size(v) < 10) {
    printf ("not 10\n");
    goto OUT_DECREF;
  }
  for(i=0; i<10; i++) {
    if (!PyLong_Check(PyTuple_GetItem(v, i)) && !PyInt_Check(PyTuple_GetItem(v, i))) {
      printf ("not int %d\n", i);
      goto OUT_DECREF;
    }
  }

  py_to_stat (v, st);

  ret = 0;
  EPILOGUE
}

static int statfs_func (struct fuse_statfs *fsstat) {
  int i;
  PyObject *v= PyObject_CallFunction (statfs_cb, "");

  PROLOGUE
  if (!PyTuple_Check (v)) {
    printf ("not tuple\n");
    goto OUT_DECREF;
  }
  if (PyTuple_Size (v)<6) {
    printf ("not 10\n");
    goto OUT_DECREF;
  }
  for (i= 0; i<6; i++) {
    if (!PyLong_Check (PyTuple_GetItem (v, i)) && !PyInt_Check (PyTuple_GetItem (v, i))) {
      printf ("not int %d\n", i);
      goto OUT_DECREF;
    }
  }

  if (fsstat!=NULL) {
    fsstat->block_size = PyInt_AsLong(PyTuple_GetItem(v, 0));
    fsstat->blocks     = PyInt_AsLong(PyTuple_GetItem(v, 1));
    fsstat->blocks_free= PyInt_AsLong(PyTuple_GetItem(v, 2));
    fsstat->files      = PyInt_AsLong(PyTuple_GetItem(v, 3));
    fsstat->files_free = PyInt_AsLong(PyTuple_GetItem(v, 4));
    fsstat->namelen    = PyInt_AsLong(PyTuple_GetItem(v, 5));
    ret= 0;
  } else {
    ret= -EINVAL;
  }
  EPILOGUE
}

static void process_cmd(struct fuse *f, struct fuse_cmd *cmd, void *data)
{
  PyInterpreterState *interp = (PyInterpreterState *) data;
  PyThreadState *state;

  PyEval_AcquireLock();
  state = PyThreadState_New(interp);
  PyThreadState_Swap(state);
  __fuse_process_cmd(f, cmd);
  PyThreadState_Clear(state);
  PyThreadState_Swap(NULL);
  PyThreadState_Delete(state);
  PyEval_ReleaseLock();
}

static void pyfuse_loop_mt(struct fuse *f)
{
  PyInterpreterState *interp;
  PyThreadState *save;

  PyEval_InitThreads();
  interp = PyThreadState_Get()->interp;
  save = PyEval_SaveThread();
  __fuse_loop_mt(f, process_cmd, interp);
  /* Not yet reached: */
  PyEval_RestoreThread(save);
}


static PyObject *
Fuse_main(PyObject *self, PyObject *args, PyObject *kw)
{
  int flags=0;
  int multithreaded=0;
  static struct fuse *fuse=NULL;

  struct fuse_operations op;

  static char  *kwlist[] = {
    "getattr", "readlink", "getdir", "mknod",
    "mkdir", "unlink", "rmdir", "symlink", "rename",
    "link", "chmod", "chown", "truncate", "utime",
    "open", "read", "write",
    "lookup", "statfs", "setattr",
    "flags", "multithreaded",
    NULL};

  memset(&op, 0, sizeof(op));

  if (!PyArg_ParseTupleAndKeywords(args, kw, "|OOOOOOOOOOOOOOOOOOOOii",
    kwlist, &getattr_cb, &readlink_cb, &getdir_cb, &mknod_cb,
    &mkdir_cb, &unlink_cb, &rmdir_cb, &symlink_cb, &rename_cb,
    &link_cb, &chmod_cb, &chown_cb, &truncate_cb, &utime_cb,
    &open_cb, &read_cb, &write_cb,
    &lookup_cb, &statfs_cb, &setattr_cb,
    &flags, &multithreaded))
    return NULL;

#define DO_ONE_ATTR(name) \
  if(name ## _cb) { \
    Py_INCREF(name ## _cb); \
    op.name = name ## _func; \
  } else { \
    op.name = NULL; \
  }

  DO_ONE_ATTR(getattr);
  DO_ONE_ATTR(setattr);
  DO_ONE_ATTR(readlink);
  DO_ONE_ATTR(getdir);
  DO_ONE_ATTR(mknod);
  DO_ONE_ATTR(mkdir);
  DO_ONE_ATTR(unlink);
  DO_ONE_ATTR(rmdir);
  DO_ONE_ATTR(symlink);
  DO_ONE_ATTR(rename);
  DO_ONE_ATTR(link);
  DO_ONE_ATTR(chmod);
  DO_ONE_ATTR(chown);
  DO_ONE_ATTR(truncate);
  DO_ONE_ATTR(utime);
  DO_ONE_ATTR(open);
  DO_ONE_ATTR(read);
  DO_ONE_ATTR(write);
  DO_ONE_ATTR(lookup);
  DO_ONE_ATTR(statfs);

  fuse = fuse_new(0, flags, &op);
  if(multithreaded)
    pyfuse_loop_mt(fuse);
  else
    fuse_loop(fuse);

  Py_INCREF(Py_None);
  return Py_None;
}

/* List of functions defined in the module */

static PyMethodDef Fuse_methods[] = {
  {"main",  (PyCFunction)Fuse_main,   METH_VARARGS|METH_KEYWORDS},
  {NULL,    NULL}    /* sentinel */
};


/* Initialization function for the module (*must* be called init_fuse) */

DL_EXPORT(void)
init_fuse(void)
{
  PyObject *m, *d;
  static PyObject *ErrorObject;

  /* Create the module and add the functions */
  m = Py_InitModule("_fuse", Fuse_methods);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);
  ErrorObject = PyErr_NewException("fuse.error", NULL, NULL);
  PyDict_SetItemString(d, "error", ErrorObject);
  PyDict_SetItemString(d, "DEBUG", PyInt_FromLong(FUSE_DEBUG));
}
