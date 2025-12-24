
import os
import logging
import pathlib, importlib.resources

def newfio(module, fn, mode=True):
    logger = logging.getLogger('mkdocs.plugins.newfio')
    file = pathlib.Path(__file__)
    root = file.parents[1]

    oldfn = getattr(module, fn)

    def newio(callback):
        def io(path, *args, **kwargs):
            path = pathlib.Path(path)
            if not root in path.parents:
                return oldfn(path, *args, **kwargs)

            package = path.relative_to(root)

            if not mode:
                package = '.'.join(package.parts)
                logger.debug('Called %s(..) from package: %s (path=%s)', oldfn.__name__, package, path)

                file = importlib.resources.files(package)
                return callback(file, *args, **kwargs)

            name = package.name
            parent = package.parent

            package = '.'.join(parent.parts)
            logger.debug('Called %s(..) from package: %s (path=%s, file=%s)', oldfn.__name__, package, path, name)

            file = importlib.resources.files(package).joinpath(name)
            return callback(file, *args, **kwargs)

        setattr(module, fn, io)
        return io

    return newio