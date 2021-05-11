## `set_of_files`

The [`set_of_files`](../_api/soxspipe.commonutils.set_of_files.html) utility helps to translate and homogenise various recipe input-frame lists. This allows recipes to accept any of the following inputs:

* an ESORex-like sof file,
* a directory of FITS files
* a list of fits file paths

Behind the scenes [`set_of_files`](../_api/soxspipe.commonutils.set_of_files.html) converts the lists into a [CCDProc ImageFileCollection](https://ccdproc.readthedocs.io/en/latest/api/ccdproc.ImageFileCollection.html).

Lines in a sof file beginning with a `#` are considered as comments and therefore ignored by the pipeline.

```eval_rst
.. autoclass:: soxspipe.commonutils.set_of_files
    :members:
```
