from paver import easy,options
from paver.easy import path,sh
from paver.options import Bunch
from jsmin import jsmin
from redis import Redis
try:
    from uglipyjs import compile as uglify
except:
    uglify = None
import json
import os

cache = Redis()

testbunch = Bunch(
        x='y',
        js_dir='js/files',
        css_indir='css/src',
        cssout='vendor/css',
)

SET_ARG = dict(ex=7200)

options.test = testbunch

options.assets = Bunch(
    css='',
    js='',
    folders=Bunch(
        js='static/js',
        css='static/css',
 
    ),
    js_files=[],
)
easy.environment.ttt = 'hnmmm'
easy.environment.assets = ''


cache_set = lambda key,val: cache.set(key,val,**SET_ARG)
cache_get = lambda key: cache.get(key)

def get_version():
    import json
    return json.loads(open('version.json','r').read()).get('version')

def set_version(version):
    print 'setting version to {}'.format(version)
    with open('version.json','w') as f:
        f.write(json.dumps(dict(version=version)))



@easy.task
@easy.cmdopts([
    ('branch=','b','a new branch to create to work on')],
    share_with=['done'])
def work_on(options,branch=None):
    if branch is None:
        branch = options.work_on.branch
    cache_set('PAVER:GIT:BRANCH',branch)
    easy.info('Switching to branch {}'.format(branch))
    sh('git checkout -b {}'.format(branch))

def finish(branch=None):
    if branch is not None:
        sh('git checkout master')
        sh('git merge {}'.format(branch))
        increment_version()

@easy.task
@easy.cmdopts([
    ('branch=','b','the current branch to merge with master')]
    ,share_with=['work_on']
)
def done(options,branch=None):
    if branch is None:
        branch = cache_get('PAVER:GIT:BRANCH') or options.done.branch 
    finish(branch)

    



@easy.task
def version():
    easy.info(get_version())

@easy.task
def increment_version():
    version = get_version()
    l,m,s = map(int,version.split('.'))
    if s == 9:
        s = 0
        if m == 9:
            m = 0
            if str(l).endswith == '9':
                l = (int(l[0]) + 1) + 0
            else:
                l += 1
        else:
            m += 1
    else:
        s += 1
    set_version('.'.join(map(str,[l,m,s])))
    


@easy.task
def print_test(arg=None):
    if arg is None:
        print options.test.js_dir
    else:
        print arg

@easy.task
def print_more():
    options.test.js_dir = 'yessss'
    easy.call_task('print_test')

@easy.task
def out1():
    easy.environment.assets = 'myassets\njbjkak\nxjbxkbk\n'

@easy.task
def out2():
    easy.call_task('out1')
    #print easy.environment.assets
    assets = easy.environment.assets.split('\n')
    easy.environment.assets = assets

@easy.task
def out3(assets):
    easy.call_task('out2')
    print easy.environment.assets


@easy.task
def get_js():
    options.assets.js_files = [(x.name,x.text()) for x in easy.path(options.assets.folders.js).files()]

@easy.task
def get_css():
    return options.assets.css

@easy.task
@easy.consume_args
def add_js_files(args,files=[]):
    for filename in args + files:
        options.assets.js += easy.path(filename).text()

@easy.task
@easy.consume_args
def show(args,ttt):
    if args:
        options.assets.folders.js = args[0]
    easy.call_task('increment_version')
    easy.call_task('get_js')
    easy.call_task('minify')
    easy.call_task('uglify')
    easy.call_task('concat')
    print get_version()


@easy.task
def minify():
    options.assets.js_files = map(lambda x: ((x[0],jsmin(x[1]))),options.assets.js_files)


@easy.task
def uglify():
    for fle,data in options.assets.js_files:
        try:
            options.assets.js_files[options.assets.js_files.index((fle,data))] = (fle,compile(data))
        except:
            print fle
            #options.assets.js_files = map(compile,options.assets.js_files)

@easy.task
def concat():
    options.assets.js = ''.join(map(lambda x: str(x[1]),options.assets.js_files))

