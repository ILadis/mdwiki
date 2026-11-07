
import os
import logging
import pathlib, importlib.resources

def newfio(module, fn, mode=True):
    logger = logging.getLogger('mkdocs.plugins.newfio')
    file = pathlib.Path(__file__)
    root = file.parents[1]

    oldfn = getattr(module, fn)

    def newio(callback):
        guard = False

        def io(oldpath, *args, **kwargs):
            nonlocal guard
            if guard:
                return oldfn(oldpath, *args, **kwargs)

            # path may be passed as bytes like object, in this case the caller expects
            # results back as bytes like objects (which is currently not implemented)
            try: path = str(oldpath, 'utf-8')
            except: path = oldpath

            path = pathlib.Path(path)
            if not root in path.parents:
                return oldfn(oldpath, *args, **kwargs)

            package = path.relative_to(root)

            if not mode:
                package = '.'.join(package.parts)
                logger.debug('Called %s(..) from package: %s (path=%s)', oldfn.__name__, package, path)

                try:
                    guard = True
                    file = importlib.resources.files(package)
                    return callback(file, *args, **kwargs)
                finally:
                    guard = False

            name = package.name
            parent = package.parent

            package = '.'.join(parent.parts)
            logger.debug('Called %s(..) from package: %s (path=%s, file=%s)', oldfn.__name__, package, path, name)

            try:
                guard = True
                file = importlib.resources.files(package).joinpath(name)
                return callback(file, *args, **kwargs)
            finally:
                guard = False

        setattr(module, fn, io)
        return io

    return newio