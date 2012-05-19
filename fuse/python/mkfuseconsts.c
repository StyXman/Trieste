#include <linux/fuse.h>
#include <stdio.h>

int main () {
  printf ("mode=  %2d\n", FATTR_MODE);
  printf ("uid=   %2d\n", FATTR_UID);
  printf ("gid=   %2d\n", FATTR_GID);
  printf ("size=  %2d\n", FATTR_SIZE);
  printf ("atime= %2d\n", FATTR_UTIME);
  printf ("mtime= %2d\n", FATTR_UTIME);

  return 0;
}
