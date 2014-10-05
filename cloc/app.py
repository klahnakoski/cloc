import re
from util.strings import indent
from util.env import startup
from util.env.files import File
from util.env.logs import Log


def replace(from_, to_, code):
    code = re.sub(from_, to_, code, flags=re.MULTILINE | re.UNICODE)
    return code


def process(file, depth=0):
    if file.name=="util":  #SPECIFIC TO ALL THAT USE THE pyLibrary
        return 0

    if file.is_directory():
        loc=0
        for f in file.children:
            try:
                loc += process(f, depth+1)
            except Exception, e:
                pass
        if loc>0:
            Log.note(indent("{{lines|right_align(8)}} loc in {{filename}}", indent=depth), {
                "lines": loc,
                "filename": file.abspath
            })
        return loc

    if file.extension not in ["py"]:
        return 0


    code = file.read()
    code = replace(r'\"\"\".*?\"\"\"', r'', code)  # REMOVE MULTILINE COMMENTS
    code = replace(r'#.*?\n', r'', code)  # REMOVE EOL COMMENTS

    old_code = None
    while (code != old_code):
        old_code = code
        code = replace(r'\n\s*?\n', r'\n', code)  # REMOVE BLANK LINES

    loc = len(code.split("\n"))
    if loc == 1 and len(code.strip()) == 0:
        loc = 0

    Log.note(indent("{{lines|right_align(8)}} loc in {{filename}}", indent=depth), {
        "lines": loc,
        "filename": file.abspath
    })
    return loc

def main():
    settings = startup.read_settings(defs=[{
        "name": ["--file", "--dir"],
        "help": "provide a file or directory",
        "dest": "files"
    }])
    Log.start(settings.debug)
    try:
        process(File(settings.args.files))
    except Exception, e:
        Log.warning("Problem converting", e)
    finally:
        Log.stop()


if __name__ == '__main__':
    main()
