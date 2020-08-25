# import threading, builtins
# printlock = threading.Lock()
#
# vanilla_print = print
# def orderly_print(*a, **k):
#     printlock.acquire()
#     try:
#         vanilla_print(*a, **k)
#     except Exception as ex:
#         printlock.release()
#         raise ex
#     else:
#         printlock.release()
#
# builtins.print = orderly_print

import time,os,sched,random,threading,traceback,datetime
import re,base64
import zlib

import requests as r

import Identicon
Identicon._crop_coner_round = lambda a,b:a # don't cut corners, please
import mimetypes as mt

from commons import *

from flask_cors import CORS

from flask import Flask, session, g
from flask import render_template, request, send_from_directory, make_response
from flask_gzip import Gzip

from werkzeug.middleware.proxy_fix import ProxyFix

from api import api_registry, get_categories_info, get_url_to_post, get_url_to_post_given_details
from api import *

# init_directory('./static/')
# init_directory('./static/upload/')

def get_secret():
    fn = 'secret.bin'
    if os.path.exists(fn):
        f = open(fn, 'rb');r = f.read();f.close()
    else:
        r = os.urandom(32)
        f = open(fn, 'wb');f.write(r);f.close()
    return r

app = Flask(__name__, static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

app.secret_key = get_secret()
CORS(app)
gzip = Gzip(app, minimum_size=500)

def route(r):
    def rr(f):
        app.add_url_rule(r, str(random.random()), f)
    return rr

# def route_static(frompath, topath):
#     @route('/'+frompath+'/<path:path>')
#     def _(path): return send_from_directory(topath, path)

def calculate_etag(bin):
    checksum = zlib.adler32(bin)
    chksum_encoded = base64.b64encode(checksum.to_bytes(4,'big')).decode('ascii')
    return chksum_encoded

def route_static(frompath, topath, maxage=1800):
    @route('/'+frompath+'/<path:path>')
    def _(path):
        cc = topath+'/'+path
        if not os.path.exists(cc):
            return make_response('File not found', 404)

        supplied_etags = request.if_none_match

        with open(cc,'rb') as f:
            b = f.read()

        etag = calculate_etag(b)

        if etag in supplied_etags: # 304 not changed
            resp = make_response('', 304)

        else:
            resp = make_response(b)

            resp.set_etag(etag)

            type, encoding = mt.guess_type(cc)
            if encoding:
                resp.headers['Content-Encoding'] = encoding
            if type:
                resp.headers['Content-Type'] = type

        if maxage!=0:
            resp.headers['Cache-Control']= 'max-age='+str(maxage)

        return resp

route_static('static', 'static')
route_static('images', 'templates/images', 3600)
route_static('css', 'templates/css', 300)
route_static('js', 'templates/js', 300)
route_static('jgawb', 'jgawb', 1800)
route_static('jicpb', 'jicpb', 1800)

aqlc.create_index('threads',
    type='persistent', fields=['t_u','t_c'], unique=False, sparse=False)
aqlc.create_index('threads',
    type='persistent', fields=['cid','t_u','t_c'], unique=False, sparse=False)

aqlc.create_index('threads',
    type='persistent', fields=['delete','t_u','t_c'], unique=False, sparse=False)
aqlc.create_index('threads',
    type='persistent', fields=['delete','cid','t_u','t_c'], unique=False, sparse=False)

aqlc.create_index('threads',
    type='persistent', fields=['uid','t_u','t_c'], unique=False, sparse=False)
aqlc.create_index('threads',
    type='persistent', fields=['tid'], unique=True, sparse=False)

aqlc.create_index('posts',
    type='persistent', fields=['tid','t_c','_key'], unique=False, sparse=False)
aqlc.create_index('posts',
    type='persistent', fields=['uid','t_c','_key'], unique=False, sparse=False)

aqlc.create_index('categories',
    type='persistent', fields=['cid'], unique=True, sparse=False)

aqlc.create_index('users',
    type='persistent', fields=['t_c','t_u'], unique=False, sparse=False)
aqlc.create_index('users',
    type='persistent', fields=['t_u','t_c'], unique=False, sparse=False)
aqlc.create_index('users',
    type='persistent', fields=['uid'], unique=True, sparse=False)
aqlc.create_index('users',
    type='persistent', fields=['name'], unique=False, sparse=False)

aqlc.create_index('users',
    type='persistent', fields=['invitation'], unique=False, sparse=False)

aqlc.create_index('invitations',
    type='persistent', fields=['uid','active','t_c'], unique=False, sparse=False)
aqlc.create_index('invitations',
    type='persistent', fields=['uid','t_c'], unique=False, sparse=False)

aqlc.create_index('votes',
    type='persistent', fields=['type','id','vote','uid'], unique=False, sparse=False)
aqlc.create_index('votes',
    type='persistent', fields=['type','id','uid','vote'], unique=False, sparse=False)
aqlc.create_index('votes',
    type='persistent', fields=['to_uid','vote','t_c'], unique=False, sparse=False)
aqlc.create_index('votes',
    type='persistent', fields=['uid','vote','t_c'], unique=False, sparse=False)

aqlc.create_index('votes',
    type='persistent', fields=['to_uid','t_c'], unique=False, sparse=False)
aqlc.create_index('votes',
    type='persistent', fields=['uid','t_c'], unique=False, sparse=False)

aqlc.create_index('conversations',
    type='persistent', fields=['uid','to_uid','t_u'], unique=False, sparse=False)
aqlc.create_index('conversations',
    type='persistent', fields=['uid','t_u'], unique=False, sparse=False)

aqlc.create_index('messages',
    type='persistent', fields=['convid','t_c'], unique=False, sparse=False)
aqlc.create_index('messages',
    type='persistent', fields=['to_uid','t_c'], unique=False, sparse=False)

aqlc.create_index('notifications',
    type='persistent', fields=['to_uid','t_c'], unique=False, sparse=False)
aqlc.create_index('notifications',
    type='persistent', fields=['to_uid','from_uid','why','url'], unique=False, sparse=False)

aqlc.create_index('avatars',
    type='persistent', fields=['uid'], unique=False, sparse=False)

is_integer = lambda i:isinstance(i, int)
class Paginator:
    def __init__(self,):
        pass

    def get_user_list(self,
        sortby='uid',
        order='desc',
        pagesize=50,
        pagenumber=1,
        path=''):

        assert sortby in ['t_c','uid'] # future can have more.
        # sortby = 't_c'
        assert order in ['desc', 'asc']

        pagenumber = max(1, pagenumber)

        start = (pagenumber-1)*pagesize
        count = pagesize

        mode = 'user'

        querystring_complex = '''
        for u in users
        sort u.{sortby} {order}
        limit {start},{count}

        let stat = {{
            nthreads:length(for t in threads filter t.uid==u.uid return t),
            nposts:length(for p in posts filter p.uid==u.uid return p),
        }}

        return merge(u, stat)
        '''.format(sortby=sortby, order=order,
        start=start, count=count,)

        querystring_simple = 'return length(for u in users return 1)'

        num_users = aql(querystring_simple, silent=True)[0]
        userlist = aql(querystring_complex, silent=True)

        pagination_obj = self.get_pagination_obj(num_users, pagenumber, pagesize, order, path, sortby, mode=mode)

        for u in userlist:
            userfill(u)
            # u['profile_string'] = u['name']

        return userlist, pagination_obj

    def get_post_list(self,
        by='thread',
        tid=0,
        uid=0,

        # sortby='t_c',
        order='desc',
        pagesize=50,
        pagenumber=1,

        path=''):

        assert by in ['thread', 'user']
        assert is_integer(tid)
        assert is_integer(uid)

        # assert sortby in ['t_c']
        sortby = 't_c'
        assert order in ['desc', 'asc']

        pagenumber = max(1, pagenumber)

        start = (pagenumber-1)*pagesize
        count = pagesize

        if by=='thread':
            filter = 'filter i.tid == {}'.format(tid)
            mode='post'
        else: # filter by user
            filter = 'filter i.uid == {}'.format(uid)
            mode='user_post'

        selfuid = g.logged_in['uid'] if g.logged_in else -1

        querystring_complex = '''
        for i in posts
        {filter}

        let u = (for u in users filter u.uid==i.uid return u)[0]
        let self_voted = length(for v in votes filter v.uid=={selfuid} and v.id==to_number(i._key) and v.type=='post' and v.vote==1 return v)

        sort i.{sortby} {order}
        limit {start},{count}
        return merge(i, {{user:u}},{{self_voted}})
        '''.format(
            selfuid = selfuid,
            sortby = sortby,order=order,start=start,count=count,filter=filter,
        )

        querystring_simple = '''
        return length(for i in posts {filter} return i)
        '''.format(filter=filter)

        count = aql(querystring_simple, silent=True)[0]
        # print('done',time.time()-ts);ts=time.time()

        postlist = aql(querystring_complex, silent=True)
        # print('done',time.time()-ts);ts=time.time()

        # uncomment if you want floor number in final output.
        # for idx, p in enumerate(postlist):
        #     p['floor_num'] = idx + start + 1

        pagination_obj = self.get_pagination_obj(count, pagenumber, pagesize, order, path, sortby, mode=mode)

        return postlist, pagination_obj

    def get_thread_list(self,
        by='category',
        category='all',
        uid=0,
        sortby='t_u',
        order='desc',
        pagesize=50,
        pagenumber=1,
        path=''):

        ts = time.time()

        assert by in ['category', 'user']
        assert category=='all' or category=='deleted' or is_integer(category)
        assert is_integer(uid)
        assert sortby in ['t_u', 't_c']
        assert order in ['desc', 'asc']

        pagenumber = max(1, pagenumber)

        start = (pagenumber-1)*pagesize
        count = pagesize

        if by=='category':
            if category=='all':
                filter = 'filter i.delete!=true'
            elif category=='deleted':
                filter = 'filter i.delete==true'
            else:
                filter = 'filter i.cid == {} and i.delete!=true'.format(category)
            mode='thread'
        else: # filter by user
            filter = 'filter i.uid == {}'.format(uid)
            mode='user_thread'

        querystring_complex = '''
        for i in threads

        let u = (for u in users filter u.uid == i.uid return u)[0]
        let fin = (for p in posts filter p.tid == i.tid sort p.t_c desc limit 1 return p)[0]
        let count = length(for p in posts filter p.tid==i.tid return p)
        let ufin = (for j in users filter j.uid == fin.uid return j)[0]
        let c = (for c in categories filter c.cid==i.cid return c)[0]

        {filter}

        sort i.{sortby} {order}
        limit {start},{count}
        return merge(unset(i,'content'), {{user:u, last:fin, lastuser:ufin, cname:c.name, count:count}})
         '''.format(
                sortby = sortby,
                order = order,
                start = start,
                count = count,
                filter = filter,
        )

        querystring_simple = '''
        return length(for i in threads {filter} return i)
        '''.format(filter=filter)

        count = aql(querystring_simple, silent=True)[0]
        # print('done',time.time()-ts);ts=time.time()

        threadlist = aql(querystring_complex, silent=True)
        # print('done',time.time()-ts);ts=time.time()

        pagination_obj = self.get_pagination_obj(count, pagenumber, pagesize, order, path, sortby, mode)

        return threadlist, pagination_obj

    def get_pagination_obj(self, count, pagenumber, pagesize, order, path, sortby, mode='thread'):
        # total number of pages
        total_pages = max(1, (count-1) // pagesize +1)

        if total_pages > 1:
            # list of surrounding numbers
            slots = [pagenumber]
            for i in range(1,9):
                if len(slots)>=9:
                    break
                if pagenumber+i <= total_pages:
                    slots.append(pagenumber+i)
                if len(slots)>=9:
                    break
                if pagenumber-i >= 1:
                    slots.insert(0, pagenumber-i)

            # first and last numbers
            slots[0] = 1
            slots[-1]=total_pages

            # second first and second last numbers
            if len(slots)>5:
                if slots[0]!=slots[2]-2:
                    slots[1] = (slots[0]+slots[2]) // 2
                if slots[-1]!=slots[-3]+2:
                    slots[-2] = (slots[-1]+slots[-3]) // 2

        else:
            slots = []

        defaults = None
        # if a parameter is at its default value,
        # don't put it into url query params
        if mode=='thread':
            defaults = thread_list_defaults
        elif mode=='post':
            defaults = post_list_defaults
        elif mode=='user_thread':
            defaults = user_thread_list_defaults
        elif mode=='user_post':
            defaults = user_post_list_defaults
        elif mode=='user':
            defaults = user_list_defaults
        else:
            raise Exception('unsupported mode')

        # querystring calculation for each of the paginator links.
        def querystring(pagenumber, pagesize, order, sortby):
            ql = [] # query list

            if pagenumber!=defaults['pagenumber']:
                ql.append(('page', pagenumber))

            if pagesize!=defaults['pagesize']:
                ql.append(('pagesize', pagesize))

            if order!=defaults['order']:
                ql.append(('order', order))

            if sortby!=defaults['sortby']:
                ql.append(('sortby', sortby))

            # join the kv pairs together
            qs = '&'.join(['='.join([str(j) for j in k]) for k in ql])

            # question mark
            if len(qs)>0:
                qs = path+'?'+qs
            else:
                qs = path

            return qs

        slots = [(i, querystring(i, pagesize, order, sortby), i==pagenumber) for i in slots]

        orders = [
            ('降序', querystring(pagenumber, pagesize, 'desc', sortby), order=='desc'),
            ('升序', querystring(pagenumber, pagesize, 'asc', sortby), order=='asc')
        ]

        sortbys = [
        ('最后回复', querystring(pagenumber, pagesize, order, 't_u'), 't_u'==sortby),
        ('发布时间', querystring(pagenumber, pagesize, order, 't_c'), 't_c'==sortby),
        ]

        sortbys2 = [
        ('UID',querystring(pagenumber, pagesize, order, 'uid'), 'uid'==sortby),
        ('注册时间', querystring(pagenumber, pagesize, order, 't_c'),'t_c'==sortby)
        ]

        button_groups = []

        if len(slots):
            button_groups.append(slots)

            if pagenumber!=1:
                button_groups.insert(0,[('上一页',querystring(pagenumber-1, pagesize, order,sortby))])

            if pagenumber!=total_pages:
                button_groups.append([('下一页',querystring(pagenumber+1, pagesize, order, sortby))])

        # no need to sort if number of items < 2
        if count>1:
            button_groups.append(orders)

        if mode=='thread' or mode=='user_thread':
            button_groups.append(sortbys)

        if mode=='user':
            button_groups.append(sortbys2)

        if count>1:
            button_groups.append([('共 {:d}'.format(count), '')])

        return {
            'button_groups':button_groups,
            'count':count,
        }

pgnt = Paginator()

def key(d, k):
    if k in d:
        return d[k]
    else:
        return None

# return requests.args[k] as int or 0
def rai(k):
    v = key(request.args,k)
    return int(v) if v else 0

# return requests.args[k] as string or ''
def ras(k):
    v = key(request.args,k)
    return str(v) if v else ''

def get_user(uid):
    uo = aql('for i in users filter i.uid==@k \
        let admin = length(for a in admins filter a.name==i.name return a)\
        return merge(i, {admin})',
        k=uid, silent=True)[0]

    return uo

# logged_in = False

# filter bots/DOSes that use a fixed UA
'''
不是我说你们，你们要是真会写代码，也不至于过来干这个，我都替你们着急啊
'''
class UAFilter:
    def __init__(self):
        self.d = {}
        self.dt = {}
        self.blacklist = ''

    def timedelta(self, ua):
        this_time = time.time()

        if ua in self.dt:
            last_time = self.dt[ua]
        else:
            last_time = this_time

        duration = max(0.001, this_time - last_time)
        self.dt[ua] = this_time

        return duration

    def cooldown(self, ua):
        duration = self.timedelta(ua)
        factor = 0.6 ** duration

        if ua in self.d:
            self.d[ua] *= factor

    def judge(self, uastring, weight=1.):
        ua = uastring

        if ua in self.d:
            self.d[ua]+=1*weight
            if ua in self.blacklist:
                self.d[ua]+=3*weight
        else:
            self.d[ua]=1

        duration = self.timedelta(ua)
        factor = 0.98 ** duration

        self.d[ua] *= factor
        # print(self.d[ua])

        # print_err(self.d[ua])
        if self.d[ua]>20:
            self.d[ua]+=3*weight

            if self.d[ua]>75 and (ua not in self.blacklist):
                self.blacklist+=ua

            return False
        else:
            return True

    def get_max(self):
        k = max(self.d)
        return k, self.d[k]

uaf = UAFilter()

@app.before_request
def befr():
    acceptstr = request.headers['Accept'] if 'Accept' in request.headers else 'NoAccept'
    uas = str(request.user_agent) if request.user_agent else 'NoUA'

    ipstr = request.remote_addr

    if 'uid' in session:
        g.logged_in = get_user(int(session['uid']))
        g.current_user = g.logged_in
        print_info(g.logged_in['name'])

        # print_err(request.headers)

        # when is the last time you check your inbox?
        if 't_inbox' not in g.current_user:
            g.current_user['t_inbox'] = '1989-06-04T00:00:00'

        # when is the last time you check your notifications?
        if 't_notif' not in g.current_user:
            g.current_user['t_notif'] = '1989-06-04T00:00:00'

        # how many unread messages/notifications?
        num_unread, num_notif = aql('''return [
            length(for m in messages filter m.to_uid==@uid and m.t_c>@lastcheck return m),
            length(for n in notifications filter n.to_uid==@uid and n.t_c>@lastcheck_n return n)
            ]''',
            uid=g.current_user['uid'],
            lastcheck=g.current_user['t_inbox'],
            lastcheck_n=g.current_user['t_notif'],
            silent=True,
        )[0]
        g.current_user['num_unread']=num_unread
        g.current_user['num_notif']=num_notif

        uaf.cooldown(uas)
        uaf.cooldown(acceptstr)
        return
    else:
        g.logged_in = False
        g.current_user = g.logged_in

    if 'action' in request.args and request.args['action']=='ping':
        uaf.cooldown(uas)
        uaf.cooldown(acceptstr)
        return

    if request.path.startswith('/avatar/'):
        return

    weight = 1.
    if 'application/x-php' in acceptstr:
        weight = 2.

    # filter bot/dos requests
    allowed = \
        uaf.judge(uas, weight) and\
        uaf.judge(acceptstr, weight) and\
        (uaf.judge(ipstr, weight) if ipstr[0:8]!='192.168.' else True)

    if not allowed:
        print_err('[{}][{}][{}][{:.2f}][{:.2f}][{:.2f}]'.format(uas, acceptstr, ipstr, uaf.d[uas], uaf.d[acceptstr], uaf.d[ipstr] if ipstr in uaf.d else -1))

        if random.random()>1:
            return ('rate limit exceeded', 500)
        elif random.random()>0.02:
            return ('please wait a moment before accesing this page'+base64.b64encode(os.urandom(int(random.random()*256))), 200)
        else:
            pass
    else:
        print_up('max: [{}][{:.2f}][{}]'.format(*uaf.get_max(), uaf.blacklist))

@app.route('/')
@app.route('/c/all')
def catall():
    pagenumber = rai('page') or thread_list_defaults['pagenumber']
    pagesize = rai('pagesize') or thread_list_defaults['pagesize']
    order = ras('order') or thread_list_defaults['order']
    sortby = ras('sortby') or thread_list_defaults['sortby']

    rpath = request.path
    # print(request.args)

    threadlist, pagination = pgnt.get_thread_list(
        by='category', category='all', sortby=sortby, order=order,
        pagenumber=pagenumber, pagesize=pagesize,
        path = rpath)

    return render_template('threadlist.html.jinja',
        page_title='所有分类',
        threadlist=threadlist,
        pagination=pagination,
        categories=get_categories_info(),
        # threadcount=count,
        **(globals())
    )

@app.route('/c/deleted')
def delall():
    pagenumber = rai('page') or thread_list_defaults['pagenumber']
    pagesize = rai('pagesize') or thread_list_defaults['pagesize']
    order = ras('order') or thread_list_defaults['order']
    sortby = ras('sortby') or thread_list_defaults['sortby']

    rpath = request.path

    threadlist, pagination = pgnt.get_thread_list(
        by='category', category='deleted', sortby=sortby, order=order,
        pagenumber=pagenumber, pagesize=pagesize,
        path = rpath)

    return render_template('threadlist.html.jinja',
        page_title='所有分类',
        threadlist=threadlist,
        pagination=pagination,
        categories=get_categories_info(),
        # threadcount=count,
        **(globals())
    )

@app.route('/u/all')
def alluser():
    pagenumber = rai('page') or 1
    pagesize = rai('pagesize') or 50
    order = ras('order') or 'desc'
    sortby = ras('sortby') or 'uid'
    rpath = request.path

    userlist, pagination = pgnt.get_user_list(
        sortby=sortby, order=order,
        pagenumber=pagenumber, pagesize=pagesize,
        path = rpath)

    return render_template('userlist.html.jinja',
        page_title='所有用户',
        # threadlist=threadlist,
        userlist = userlist,
        pagination=pagination,
        # threadcount=count,
        **(globals())
    )

@app.route('/p/<int:pid>')
def getpost(pid):
    url = get_url_to_post(str(pid))
    resp = make_response('', 307)
    resp.headers['Location'] = url
    resp.headers['Cache-Control']= 'max-age=86400'
    return resp

@app.route('/p/<int:pid>/code')
def getpostcode(pid):
    p = aql('for p in posts filter p._key==@k return p',k=str(pid), silent=True)[0]
    resp = make_response(p['content'], 200)
    resp.headers['Cache-Control']='max-age=1800'
    resp.headers['Content-Type']='text/plain; charset=UTF-8'
    return resp

@app.route('/t/<int:tid>/code')
def getthreadcode(tid):
    p = aql('for p in threads filter p.tid==@k return p',k=tid, silent=True)[0]
    resp = make_response(p['content'], 200)
    resp.headers['Cache-Control']='max-age=1800'
    resp.headers['Content-Type']='text/plain; charset=UTF-8'
    return resp

@app.route('/c/<int:cid>')
def catspe(cid):
    catobj = aql('for c in categories filter c.cid==@cid return c',cid=cid, silent=True)

    if len(catobj)!=1:
        return make_response('category not exist', 404)

    catobj = catobj[0]

    pagenumber = rai('page') or 1
    pagesize = rai('pagesize') or 30
    order = ras('order') or 'desc'
    sortby = ras('sortby') or 't_u'

    rpath = request.path
    # print(request.args)

    threadlist, pagination = pgnt.get_thread_list(
        by='category', category=cid,
        sortby=sortby,
        order=order,
        pagenumber=pagenumber, pagesize=pagesize,
        path = rpath)

    return render_template('threadlist.html.jinja',
        page_title=catobj['name'],
        page_subheader=(catobj['brief'] or '').replace('\\',''),
        threadlist=threadlist,
        pagination=pagination,
        categories=get_categories_info(),
        category=catobj,
        # threadcount=count,
        **(globals())
    )

@app.route('/u/<int:uid>/t')
def userthreads(uid):
    uobj = aql('''
    for u in users filter u.uid==@uid
    return u
    ''', uid=uid, silent=True)

    if len(uobj)!=1:
        return make_response('user not exist', 404)

    uobj = uobj[0]

    pagenumber = rai('page') or 1
    pagesize = rai('pagesize') or 30
    order = ras('order') or 'desc'
    sortby = ras('sortby') or 't_c'

    rpath = request.path
    # print(request.args)

    threadlist, pagination = pgnt.get_thread_list(
        by='user', uid=uid,
        sortby=sortby,
        order=order,
        pagenumber=pagenumber, pagesize=pagesize,
        path = rpath)

    return render_template('threadlist.html.jinja',
        # page_title=catobj['name'],
        page_title='帖子 - '+uobj['name'],
        threadlist=threadlist,
        pagination=pagination,
        # threadcount=count,
        **(globals())
    )

# thread, list of posts
@app.route('/t/<int:tid>')
def thrd(tid):

    selfuid = g.logged_in['uid'] if g.logged_in else -1

    thobj = aql('''
    for t in threads filter t.tid==@tid
    let u = (for u in users filter u.uid==t.uid return u)[0]

    let self_voted = length(for v in votes filter v.uid==@selfuid and v.id==to_number(t.tid) and v.type=='thread' and v.vote==1 return v)

    return merge(t, {user:u},{self_voted:self_voted})
    ''', tid=tid, selfuid=selfuid, silent=True)

    if len(thobj)!=1:
        return make_response('thread not exist', 404)

    thobj = thobj[0]

    catobj = aql('''
    for c in categories filter c.cid==@cid return c
    ''', cid=thobj['cid'], silent=True)[0]
    thobj['category'] = catobj

    pagenumber = rai('page') or 1
    pagesize = rai('pagesize') or 50
    order = ras('order') or 'asc'
    # sortby = ras('sortby') or 't_u'

    rpath = request.path

    postlist, pagination = pgnt.get_post_list(
        by='thread',
        tid=tid,
        # sortby=sortby,
        order=order,
        pagenumber=pagenumber, pagesize=pagesize,
        path = rpath)

    # remove duplicate brief string within a page
    bd = dict()
    for p in postlist:
        if 'brief' in p['user']:
            b = p['user']['brief']
            if b in bd:
                p['user']['brief']=''
            else:
                bd[b] = 1

    return render_template('postlist.html.jinja',
        page_title=thobj['title'],
        # threadlist=threadlist,
        postlist=postlist,
        pagination=pagination,
        t=thobj,
        # threadcount=count,
        **(globals())
    )

# list of user posts.
@app.route('/u/<int:uid>/p')
def uposts(uid):
    uobj = aql('''
    for u in users filter u.uid==@uid
    return u
    ''', uid=uid, silent=True)

    if len(uobj)!=1:
        return make_response('user not exist', 404)

    uobj = uobj[0]

    pagenumber = rai('page') or 1
    pagesize = rai('pagesize') or 50
    order = ras('order') or 'desc'
    # sortby = ras('sortby') or 't_u'

    rpath = request.path

    postlist, pagination = pgnt.get_post_list(
        # by='thread',
        by='user',
        # tid=tid,
        uid=uid,
        # sortby=sortby,
        order=order,
        pagenumber=pagenumber, pagesize=pagesize,
        path = rpath)

    return render_template('postlist.html.jinja',
        page_title='回复 - '+uobj['name'],
        # threadlist=threadlist,
        postlist=postlist,
        pagination=pagination,
        # t=thobj,
        u=uobj,
        # threadcount=count,
        **(globals())
    )

@app.route('/editor')
def editor_handler():
    details = dict()
    details['has_title'] = True

    target = ras('target')
    target_type, _id = parse_target(target, force_int=False)

    if target_type not in [
        'user','username','edit_post','edit_thread','category','thread'
        ]:
        raise Exception('unsupported target_type')

    if target_type=='edit_post':
        details['has_title'] = False
        post_original = aqlc.from_filter('posts', 'i._key==@_id', _id=str(_id))[0]

        details['content'] = post_original['content']

    if target_type == 'edit_thread':
        _id = int(_id)
        thread_original = aqlc.from_filter('threads', 'i.tid==@id',id=_id)[0]

        details['content'] = thread_original['content']
        details['title'] = thread_original['title']

    if target_type=='user':
        _id = int(_id)

    if 'user' in target_type:
        details['has_title'] = False

    page_title = '{} - {}'.format(
        '发表' if 'edit' not in target_type else '编辑',
        target)

    return render_template('editor.html.jinja',
        page_title = page_title,
        target=target,
        details=details,
        **(globals())
    )

def userfill(u):
    if 't_c' not in u: # some user data are incomplete
        u['t_c'] = '1989-06-04T00:00:00'
        u['brief'] = '此用户的数据由于各种可能的原因，在github上2049bbs.xyz的备份中找不到，所以就只能像现在这样处理了'

@app.route('/u/<int:uid>')
def userpage(uid):
    return _userpage(uid)

def _userpage(uid):
    uobj = aql('''
    for u in users filter u.uid==@uid
    return u
    ''', uid=uid, silent=True)

    if len(uobj)!=1:
        return make_response('user not exist', 404)

    uobj = uobj[0]
    u = uobj

    userfill(u)
    user_is_self = (uid == g.logged_in['uid']) if g.logged_in else False

    stats = aql('''return {
            nthreads:length(for t in threads filter t.uid==@uid return t),
            nposts:length(for p in posts filter p.uid==@uid return p),
        }
        ''',uid=uid, silent=True)[0]

    uobj['stats']=stats
    invitations = None
    if g.logged_in:
        if user_is_self:
            k = aql('for i in invitations filter i.uid==@k\
            let users = (for u in users filter u.invitation==i._key return u)\
            sort i.t_c desc limit 25 return merge(i,{users})',k=uid,silent=True)
            invitations = k

    return render_template('userpage.html.jinja',
        page_title=uobj['name'],
        u=uobj,
        invitations=invitations,
        user_is_self=user_is_self,
        **(globals())
    )
@app.route('/register')
def regpage():
    invitation = ras('code') or ''

    return render_template('register.html.jinja',
        invitation=invitation,
        page_title='注册',
        **(globals())
    )

@app.route('/login')
def loginpage():
    username = ras('username') or ''

    return render_template('login.html.jinja',
        username=username,
        page_title='登录',
        **(globals())
    )
# print(ptf('2020-07-19T16:00:00'))

@route('/avatar/<int:uid>')
def _(uid):
    supplied_etags = request.if_none_match

    # first check db
    res = aql('for a in avatars filter a.uid==@uid return a', uid=uid, silent=True)
    # print(res)
    if len(res)>0:
        res = res[0]

        if 'data_new' in res:
            # new 2047 png pipeline
            d = res['data_new']
            rawdata = base64.b64decode(d)

            resp = make_response(rawdata, 200)
            resp.headers['Content-Type'] = 'image/png'
        elif 'data' in res:
            # old 2049bbs jpeg pipeline

            d = res['data']
            match = re.match(r'^data:(.*?);base64,(.*)$',d)
            mime,b64data = match[1],match[2]

            rawdata = base64.b64decode(b64data)

            resp = make_response(rawdata, 200)
            resp.headers['Content-Type'] = 'image/jpeg'

        else:
            raise Exception('no data in avatar object found')

    else: # db no match
        # render an identicon
        identicon = Identicon.render(str(uid*uid))
        resp = make_response(identicon, 200)
        resp.headers['Content-Type'] = 'image/png'

    etag = calculate_etag(resp.data)
    if etag in supplied_etags:
        resp = make_response('', 304)
    else:
        resp.set_etag(etag)

    if 'no-cache' in request.args:
        resp.headers['Cache-Control']= 'no-cache'
    else:
        resp.headers['Cache-Control']= 'max-age=14400'
    return resp

    # default: 307 to logo.png
    resp = make_response(
        'no avatar obj found for uid {}'.format(uid), 307)
    resp.headers['Location'] = '/images/logo.png'
    resp.headers['Cache-Control']= 'max-age=1800'
    return resp

@app.route('/member/<string:name>')
def userpage_byname(name):
    # check if user exists
    res = aql('for u in users filter u.name==@n return u', n=name)
    if len(res)==0:
        return make_response('no such user', 500)

    u = res[0]
    return _userpage(u['uid'])

@app.route('/m')
def conversation_page():
    if not g.logged_in: raise Exception('not logged in')

    res = aql('''
    for i in conversations
    filter i.uid==@uid

    sort i.t_u desc

    let last = (for m in messages filter m.convid==i.convid
    sort m.t_c desc limit 1 return m)[0]

    let count = length(for m in messages filter m.convid==i.convid
    return m)

    let user = (for u in users filter u.uid==last.uid return u)[0]
    let to_user = (for u in users filter u.uid==last.to_uid return u)[0]

    return merge(i, {count, last: merge(last, {user:user, to_user:to_user})})
    ''', uid=g.logged_in['uid'],silent=True)

    # update t_inbox
    timenow = time_iso_now()
    aql('update @user with {t_inbox:@t} in users',
        user=g.current_user,t=timenow,silent=True)
    g.current_user['num_unread']=0

    return render_template('conversations.html.jinja',
        page_title='私信（测试中）',
        conversations=res,
        can_send_message=True,
        **(globals())
    )

@app.route('/m/<string:convid>')
def messages_by_convid(convid):
    if not g.logged_in: raise Exception('not logged in')
    uid = g.current_user['uid']

    # only allow user to see own conversation
    c = aql('for i in conversations filter i.convid==@k return i', k=convid, silent=True)
    if len(c)==0:
        raise Exception('convid not found')

    conv = c[0]
    if conv['uid']!=uid and conv['to_uid']!=uid:
        raise Exception('you dont own the conversation')

    res = aql('''
    for i in messages
    filter i.convid==@convid
    sort i.t_c desc

    let user = (for u in users filter u.uid==i.uid return u)[0]
    let to_user = (for u in users filter u.uid==i.to_uid return u)[0]

    return merge(i,{user, to_user})
    ''', convid=convid, silent=True)

    last = res[0]
    u1n = last['user']['name']
    u2n = last['to_user']['name']

    if uid==last['user']['uid']:
        myname = u1n
        hisname = u2n
    else:
        myname = u2n
        hisname = u1n

    return render_template('messages.html.jinja',
        page_title='和 {} 之间的私信对话'.format(hisname),
        conversation=c,
        hisname=hisname,
        editor_target = dict(
            target = 'username/{}'.format(hisname),
            uid=uid,
        ),
        messages=res,
        **(globals())
    )

@app.route('/n')
def notification_page():
    if not g.logged_in: raise Exception('not logged in')
    uid = g.current_user['uid']

    notifications = aql('for i in notifications \
    filter i.to_uid==@uid sort i.t_c desc limit 50 \
    let from_user=(for u in users filter u.uid==i.from_uid return u)[0]\
    return merge(i,{from_user})',
        uid=uid,
        silent=False)

    # update t_notif
    timenow = time_iso_now()
    aql('update @user with {t_notif:@t} in users',
        user=g.current_user,t=timenow,silent=True)
    g.current_user['num_notif']=0

    return render_template('notifications.html.jinja',
        page_title='系统提醒',
        notifications=notifications,
        **(globals()),
    )

def e(s): return make_response({'error':s}, 500)

@app.route('/api', methods=['GET', 'POST'])
def apir():

    if request.method not in ['GET','POST']:
        return e('support GET and POST only')

    if request.content_length:
        if request.content_length > 1024*1024*3: # 3MB limit
            return e('request too large')

    j = request.get_json(silent=False)

    if j is None:
        if request.method=='POST':
            return e('empty body for post')
        else: # GET
            if 'action' not in request.args:
                return e('action not specified in url params')
            else:
                j = {}
                for k in request.args:
                    j[k] = request.args[k]
    else:
        if 'action' not in j:
            return e('action not specified in json')

    # print(j)
    action = j['action']
    j['logged_in'] = g.logged_in
    if action in api_registry:
        if action != 'ping':
            print_up('API >>', j)
            g.j = j

        try:
            answer = api_registry[action]()

        except Exception as ex:
            traceback.print_exc()
            errstr = ex.__class__.__name__+'/{}'.format(str(ex))
            print_err('Exception in api "{}":'.format(action), errstr)
            return e(errstr)

        else:
            if answer is None:
                raise Exception('return value is None, what the fuck?')
            if action != 'ping':
                print_down('API <<', answer)
            if 'setuid' in answer:
                session['uid'] = answer['setuid']
            if 'logout' in answer:
                if 'uid' in session:
                    del session['uid']

            return answer
    else:
        return e('action function not registered')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method != 'POST':
        return e('please use POST')
    if not g.logged_in: raise Exception('log in please')

    data = request.data # binary
    # print(len(data))

    from imgproc import avatar_pipeline

    png = avatar_pipeline(data)
    png = base64.b64encode(png).decode('ascii')

    avatar_object = dict(
        uid=g.logged_in['uid'],
        data_new=png,
    )
    aql('upsert {uid:@uid} insert @k update @k into avatars',
        uid=avatar_object['uid'], k=avatar_object)
    return {'error':False}

@app.errorhandler(404)
def e404(e):
    return render_template('404.html.jinja',
        **(globals())
    ), 404
@app.errorhandler(500)
def e404(e):
    return render_template('404.html.jinja',
        e500=True,
        **(globals())
    ), 500

if __name__ == '__main__':
    import os
    if 'DEBUG' in os.environ:
        app.run(host='0.0.0.0', port='5000', debug=True)
    else:
        app.run(host='0.0.0.0', port='5000')
