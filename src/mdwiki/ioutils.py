
import os
import pathlib, importlib

def newfio(module, fn, mode=True):
    file = pathlib.Path(__file__)
    root = file.parents[1]

    oldfn = getattr(module, fn)

    def newio(callback):
        def io(path, *args, **kwargs):
            path = pathlib.Path(path)
            if not root in path.parents:
                return oldfn(path, *args, **kwargs)

            anchor = str(path.relative_to(root))

            if not mode:
                print(f"{oldfn}() from package: {anchor}, path is: {path}")

                file = importlib.resources.files(anchor)
                return callback(file, *args, **kwargs)

            name = os.path.basename(anchor)
            anchor = os.path.dirname(anchor).replace('/', '.')

            print(f"{oldfn}() from package: {anchor}, file is: {name}, path is: {path}")

            file = importlib.resources.files(anchor).joinpath(name)
            return callback(file, *args, **kwargs)

        setattr(module, fn, io)
        return io

    return newio